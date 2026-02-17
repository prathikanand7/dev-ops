import json
from celery import shared_task
from notebook_platform.settings import WORKER_CALLBACK_URL
from .models import Job
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

def get_absolute_url(base_url, file_url):
    if file_url.startswith('http'):
        return file_url
    
    base = base_url.rstrip('/')
    path = file_url.lstrip('/')
    return f"{base}/{path}"

@shared_task
def dispatch_job_task(job_id):
    """
    Submits a Kubernetes Job to execute the notebook.
    """
    try:
        job_record = Job.objects.get(id=job_id)
        job_record.status = 'PROVISIONING'
        job_record.save()

        try:
            config.load_incluster_config()
            print("Successfully loaded in-cluster Kubernetes configuration (AWS/Production).")
        except ConfigException:
            config.load_kube_config()
            print("Successfully loaded local kubeconfig file (Minikube/Local).")

        k8s_batch_v1 = client.BatchV1Api()
        base_url = WORKER_CALLBACK_URL
        
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
        
        k8s_job_name = f"job-{str(job_id)[:8]}" 
        
        container = client.V1Container(
            name="notebook-worker",
            image="r-notebook-worker",
            image_pull_policy="IfNotPresent", 
            command=["python"],
            args=["worker.py"], 
            working_dir="/app",
            env=[
                client.V1EnvVar(
                    name="JOB_PARAMETERS",
                    value=json.dumps(payload)
                )
            ],
        )

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": "notebook-runner"}),
            spec=client.V1PodSpec(
                containers=[container],
                restart_policy="Never"
            )
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
        
        print(f"Kubernetes Job {k8s_job_name} created for Job {job_id}")

    except Exception as e:
        print(f"Failed to dispatch job: {e}")
        job_record = Job.objects.get(id=job_id)
        job_record.status = 'FAILED'
        job_record.logs = str(e)
        job_record.save()