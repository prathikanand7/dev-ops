from celery import shared_task
from django.conf import settings
from .models import Job
import json
from kubernetes import client, config

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
        except:
            config.load_kube_config()

        k8s_batch_v1 = client.BatchV1Api()

        base_url = "http://host.docker.internal:8000"
        
        payload = {
            "_notebook_url": f"{base_url}{job_record.notebook.notebook_file.url}",
            "_notebook_filename": job_record.notebook.notebook_file.name.split('/')[-1],
            "_job_id": str(job_id),       
            "_base_url": base_url,        
            **job_record.job_parameters
        }
        if job_record.notebook.environment_file:
            payload["_environment_url"] = f"{base_url}{job_record.notebook.environment_file.url}"
        
        k8s_job_name = f"job-{str(job_id)[:8]}" 
        
        container = client.V1Container(
            name="notebook-worker",
            image="r-notebook-worker",
            image_pull_policy="Never",
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