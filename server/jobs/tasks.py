import json
import os
from celery import shared_task
from notebook_platform.settings import ENVIRONMENT, LOCAL_KUBECTL_PROXY_URL, WORKER_CALLBACK_URL, WORKER_IMAGE
from .models import Job
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException
from django.conf import settings

def get_absolute_url(base_url, file_url):
    if file_url.startswith('http'):
        return file_url
    
    base = base_url.rstrip('/')
    path = file_url.lstrip('/')
    return f"{base}/{path}"

# TODO: Refactor to decrease cognitive complexity
@shared_task
def dispatch_job_task(job_id):
    """
    Submits a Kubernetes Job to execute the notebook.
    Different behavior based on ENVIRONMENT.
    """
    try:
        job_record = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        print(f"Task aborted: Job {job_id} does not exist in the database.")
        return
    
    try:
        job_record.status = 'PROVISIONING'
        job_record.save()

        # Kubernetes Authentication
        if ENVIRONMENT == "local":
            # Bypass authentication for local Minikube with kubectl proxy
            configuration = client.Configuration()
            configuration.host = LOCAL_KUBECTL_PROXY_URL
            api_client = client.ApiClient(configuration)
            k8s_batch_v1 = client.BatchV1Api(api_client) 
            print("Successfully connected to local kubectl proxy.")
        else:
            # In production, using AWS IAM
            try:
                config.load_incluster_config()
                print("Successfully loaded in-cluster Kubernetes configuration.")
            except ConfigException:
                config.load_kube_config()
                print("Successfully loaded local kubeconfig file.")
            
            # Create the client using the AWS settings
            k8s_batch_v1 = client.BatchV1Api() 


        base_url = WORKER_CALLBACK_URL
        
        # Prepare payload for papermill
        notebook_url = get_absolute_url(base_url, job_record.notebook.notebook_file.url)
        
        payload = {
            "_notebook_url": notebook_url,
            "_notebook_filename": job_record.notebook.notebook_file.name.split('/')[-1],
            "_job_id": str(job_id),       
            "_base_url": base_url,        
            **job_record.job_parameters
        }
        
        if job_record.notebook.environment_file:
            env_url = get_absolute_url(base_url, job_record.notebook.environment_file.url)
            payload["_environment_url"] = env_url
            
        # Translation of Minio URL for local dev
        if ENVIRONMENT == "local":
            for key, val in payload.items():
                if isinstance(val, str) and "localhost:9000" in val:
                    unsigned_url = val.split('?')[0]
                    payload[key] = unsigned_url.replace("localhost:9000", "host.minikube.internal:9000")
        # ---------------------------------------

        k8s_job_name = f"job-{str(job_id)[:8]}"
        
        # Resource allocation based on environment
        if ENVIRONMENT == "production":
            resources = client.V1ResourceRequirements(
                requests={"cpu": "1", "memory": "2Gi"}, 
                limits={"cpu": "4", "memory": "16Gi"}   
            )
            worker_image = WORKER_IMAGE
            pull_policy = "Always"
        else:
            resources = client.V1ResourceRequirements(
                requests={"cpu": "250m", "memory": "512Mi"}, 
                limits={"cpu": "2", "memory": "4Gi"}   
            )
            worker_image = WORKER_IMAGE
            pull_policy = "IfNotPresent"

        container = client.V1Container(
            name="notebook-worker",
            image=worker_image,
            image_pull_policy=pull_policy, 
            command=["python"],
            args=["worker.py"], 
            working_dir="/app",
            resources=resources, 
            env=[
                client.V1EnvVar(
                    name="JOB_PARAMETERS",
                    value=json.dumps(payload)
                ),
                client.V1EnvVar(
                    name="WORKER_TOKEN",
                    value=settings.WORKER_WEBHOOK_SECRET
                )
            ],
        )

        pod_spec_kwargs = {
            "containers": [container],
            "restart_policy": "Never",
            "service_account_name": "notebook-worker-sa"
        }

        # Karpenter configuration ---- PROD ONLY
        if ENVIRONMENT == "production":
            toleration = client.V1Toleration(
                key="workload-type",
                operator="Equal",
                value="light-notebook",
                effect="NoSchedule"
            )
            pod_spec_kwargs["node_selector"] = {"workload-type": "light-notebook"}
            pod_spec_kwargs["tolerations"] = [toleration]

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": "notebook-runner"}),
            spec=client.V1PodSpec(**pod_spec_kwargs)
        )

        job_spec = client.V1JobSpec(
            template=template,
            backoff_limit=0,
            ttl_seconds_after_finished=3600 
        )

        job_obj = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=k8s_job_name),
            spec=job_spec
        )

        k8s_batch_v1.create_namespaced_job(
            namespace="default", 
            body=job_obj
        )
        
        print(f"Kubernetes Job {k8s_job_name} created for Job {job_id}. Environment: {ENVIRONMENT.upper()}")

    except Exception as e:
        print(f"Failed to dispatch job: {e}")
        try:
            job_record = Job.objects.get(id=job_id)
            job_record.status = 'FAILED'
            job_record.logs = str(e)
            job_record.save()
        except Job.DoesNotExist:
            pass