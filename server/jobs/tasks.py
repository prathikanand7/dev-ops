from celery import shared_task
from notebook_platform.settings import WORKER_CALLBACK_URL, ENVIRONMENT
from .models import Job
from .utils import get_k8s_batch_client, build_worker_payload, build_k8s_job_spec

@shared_task
def dispatch_job_task(job_id):
    """
    Orchestrates the submission of a Kubernetes Job to execute a notebook.
    """
    try:
        job_record = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        print(f"Task aborted: Job {job_id} does not exist in the database.")
        return

    try:
        job_record.status = 'PROVISIONING'
        job_record.save()

        # Authenticate with K8s
        k8s_batch_v1 = get_k8s_batch_client()

        # Build the payload and Job manifest
        payload = build_worker_payload(job_record, WORKER_CALLBACK_URL)
        job_manifest = build_k8s_job_spec(job_id, payload)

        # Submit to the cluster
        k8s_batch_v1.create_namespaced_job(namespace="default", body=job_manifest)
        
        print(f"Kubernetes Job '{job_manifest.metadata.name}' created. Environment: {ENVIRONMENT.upper()}")

    except Exception as e:
        print(f"Failed to dispatch job: {e}")
        job_record.status = 'FAILED'
        job_record.logs = str(e)
        job_record.save()