from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
import boto3
from botocore.exceptions import ClientError
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from drf_spectacular.utils import extend_schema, inline_serializer

from jobs.serializers import JobSerializer
from jobs.models import Job
from .is_kubernetes_worker import IsKubernetesWorker


AWS_BATCH_TO_INTERNAL_STATUS = {
    "SUBMITTED": "PENDING",
    "PENDING": "PENDING",
    "RUNNABLE": "PROVISIONING",
    "STARTING": "PROVISIONING",
    "RUNNING": "RUNNING",
    "SUCCEEDED": "SUCCESS",
    "FAILED": "FAILED",
}


class JobViewSet(viewsets.ModelViewSet):
    """
    Provides GET /api/jobs/, GET /api/jobs/<id>/, DELETE /api/jobs/<id>/
    """
    serializer_class = JobSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Job.objects.filter(user=self.request.user).order_by('-created_at')

    def _is_batch_job(self, job):
        params = job.job_parameters or {}
        return params.get("execution_profile") == "ec2_200gb" and bool(params.get("batch_job_id"))

    def _aws_client_kwargs(self):
        kwargs = {"region_name": settings.AWS_BATCH_TRIGGER_REGION}
        access_key = getattr(settings, "AWS_BATCH_TRIGGER_ACCESS_KEY_ID", None)
        secret_key = getattr(settings, "AWS_BATCH_TRIGGER_SECRET_ACCESS_KEY", None)
        session_token = getattr(settings, "AWS_BATCH_TRIGGER_SESSION_TOKEN", None)

        if access_key and secret_key:
            kwargs["aws_access_key_id"] = access_key
            kwargs["aws_secret_access_key"] = secret_key
            if session_token:
                kwargs["aws_session_token"] = session_token
        return kwargs

    def _refresh_batch_status(self, job):
        if not self._is_batch_job(job):
            return job

        params = dict(job.job_parameters or {})
        batch_job_id = params.get("batch_job_id")
        batch_client = boto3.client("batch", **self._aws_client_kwargs())
        describe = batch_client.describe_jobs(jobs=[batch_job_id])
        batch_jobs = describe.get("jobs", [])
        if not batch_jobs:
            return job

        batch_job = batch_jobs[0]
        batch_status = batch_job.get("status", "PENDING")
        mapped_status = AWS_BATCH_TO_INTERNAL_STATUS.get(batch_status, "PENDING")

        container = batch_job.get("container") or {}
        log_stream = container.get("logStreamName")
        status_reason = batch_job.get("statusReason") or container.get("reason")

        params["batch_status"] = batch_status
        if log_stream:
            params["batch_log_stream"] = log_stream
        if status_reason:
            params["batch_status_reason"] = status_reason

        fields_to_update = []
        if job.status != mapped_status:
            job.status = mapped_status
            fields_to_update.append("status")

        if params != (job.job_parameters or {}):
            job.job_parameters = params
            fields_to_update.append("job_parameters")

        if mapped_status in ("SUCCESS", "FAILED") and job.finished_at is None:
            job.finished_at = timezone.now()
            fields_to_update.append("finished_at")

        if mapped_status == "FAILED" and status_reason:
            job.logs = status_reason
            fields_to_update.append("logs")
        elif (job.logs or "").startswith("AWS status refresh error:"):
            # Clear stale credential/polling errors once refresh succeeds.
            job.logs = ""
            fields_to_update.append("logs")

        if fields_to_update:
            job.save(update_fields=fields_to_update)
        return job

    def _get_batch_logs(self, job, limit=200):
        job = self._refresh_batch_status(job)
        params = job.job_parameters or {}
        log_stream = params.get("batch_log_stream")
        if not log_stream:
            return job.logs or "No logs available yet..."

        logs_client = boto3.client("logs", **self._aws_client_kwargs())
        try:
            events = logs_client.get_log_events(
                logGroupName="/aws/batch/job",
                logStreamName=log_stream,
                limit=limit,
                startFromHead=True,
            ).get("events", [])
        except ClientError as exc:
            error_code = ((exc.response or {}).get("Error") or {}).get("Code")
            if error_code == "ResourceNotFoundException":
                return job.logs or "No logs available yet..."
            raise

        logs_text = "\n".join(event.get("message", "") for event in events).strip()
        if logs_text:
            if logs_text != (job.logs or ""):
                job.logs = logs_text
                job.save(update_fields=["logs"])
            return logs_text
        return job.logs or "No logs available yet..."

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if self._is_batch_job(instance):
            try:
                self._refresh_batch_status(instance)
            except Exception as exc:
                instance.logs = f"AWS status refresh error: {exc}"
                instance.save(update_fields=["logs"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(exclude=True) # Hides this overridden method from Swagger UI
    def create(self, request, *args, **kwargs):
        return Response({"error": "Jobs must be created by triggering a notebook."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @extend_schema(
        summary="Poll Recent Jobs Status",
        description="Returns a lightweight list of the user's 50 most recent jobs and their current status.",
        responses={
            200: inline_serializer(
                name='JobPollResponse',
                fields={
                    'jobs': inline_serializer(
                        name='JobPollItem',
                        fields={
                            'id': serializers.UUIDField(),
                            'status': serializers.CharField(),
                            'file_url': serializers.CharField(allow_null=True, required=False)
                        },
                        many=True
                    )
                }
            )
        }
    )
    @action(detail=False, methods=['get'])
    def poll_status(self, request):
        jobs = self.get_queryset()[:50]
        job_data = []
        for job in jobs:
            if self._is_batch_job(job):
                try:
                    self._refresh_batch_status(job)
                except Exception as exc:
                    job.logs = f"AWS status refresh error: {exc}"
                    job.save(update_fields=["logs"])
            file_url = None
            if job.output_file:
                try:
                    file_url = job.output_file.url
                except Exception:
                    pass
            job_data.append({
                'id': str(job.id),
                'status': job.status,
                'file_url': file_url
            })
        return Response({'jobs': job_data})

    @extend_schema(
        summary="Get Job Status",
        description="Returns normalized status fields for a specific job.",
        responses={
            200: inline_serializer(
                name='JobStatusResponse',
                fields={
                    'job_id': serializers.UUIDField(),
                    'status': serializers.CharField(),
                    'logs': serializers.CharField(required=False),
                    'download_url': serializers.CharField(required=False),
                    'error_message': serializers.CharField(required=False),
                }
            )
        }
    )
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        job = self.get_object()
        logs_text = job.logs or "No logs available yet..."
        if self._is_batch_job(job):
            try:
                self._refresh_batch_status(job)
                logs_text = self._get_batch_logs(job)
            except Exception as exc:
                job.logs = f"AWS status refresh error: {exc}"
                job.save(update_fields=["logs"])
                logs_text = job.logs

        response_payload = {
            "job_id": str(job.id),
            "status": job.status,
            "logs": logs_text,
        }

        if job.output_file:
            try:
                response_payload["download_url"] = job.output_file.url
            except Exception:
                pass

        if job.status == "FAILED":
            response_payload["error_message"] = job.logs or "Execution failed."

        return Response(response_payload)

    @extend_schema(
        summary="Get Job Logs",
        description="Returns the raw execution text logs for a specific job.",
        responses={
            200: inline_serializer(
                name='JobLogsResponse',
                fields={'logs': serializers.CharField()}
            )
        }
    )
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        job = self.get_object()
        if self._is_batch_job(job):
            try:
                return Response({'logs': self._get_batch_logs(job)})
            except Exception as exc:
                error_msg = f"AWS logs retrieval error: {exc}"
                job.logs = error_msg
                job.save(update_fields=["logs"])
                return Response({'logs': error_msg})
        return Response({'logs': job.logs or "No logs available yet..."})

    @extend_schema(
        summary="Job Complete Webhook",
        description="Webhook intended for the Kubernetes worker to post execution results. Secured via shared secret header.",
        request={
            'multipart/form-data': inline_serializer(
                name='JobCompleteWebhookPayload',
                fields={
                    'status': serializers.CharField(required=False, help_text="Defaults to SUCCESS"),
                    'logs': serializers.CharField(required=False),
                    'output_file': serializers.FileField(required=False)
                }
            )
        },
        responses={
            200: inline_serializer(
                name='JobCompleteResponse',
                fields={'message': serializers.CharField()}
            )
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsKubernetesWorker], authentication_classes=[])
    def complete(self, request, pk=None):
        job = get_object_or_404(Job, id=pk)
        
        job.status = request.data.get('status', 'SUCCESS')
        job.logs = request.data.get('logs', '')
        
        if 'output_file' in request.FILES:
            job.output_file = request.FILES['output_file']
            
        job.save()
        return Response({"message": f"Job {job.id} updated successfully."})
