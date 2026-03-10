import os
import uuid
import json
import base64
import boto3
from django.core.files.storage import default_storage
from django.db import transaction
from django.conf import settings
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from drf_spectacular.utils import extend_schema, inline_serializer
from drf_spectacular.types import OpenApiTypes

from jobs.models import Job, Notebook
from jobs.serializers import NotebookSerializer
from jobs.tasks import dispatch_job_task
from jobs.utils import parse_notebook_parameters, parse_notebook_parameters_from_payload, get_safe_url

EXECUTION_PROFILE_ALIASES = {
    "standard": "standard",
    "default": "standard",
    "fargate": "standard",
    "ec2_200gb": "ec2_200gb",
    "ec2-200gb": "ec2_200gb",
    "ec2_200": "ec2_200gb",
    "high-storage": "ec2_200gb",
}


def normalize_execution_profile(raw_profile):
    normalized_key = (raw_profile or "standard").strip().lower()
    return EXECUTION_PROFILE_ALIASES.get(normalized_key)


def _build_multipart_body(form_fields, form_files):
    boundary = f"----NotebookPlatformBoundary{uuid.uuid4().hex}"
    body = bytearray()

    for field_name, field_value in form_fields:
        safe_name = str(field_name).replace('"', "")
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{safe_name}"\r\n\r\n'.encode("utf-8"))
        body.extend(str(field_value).encode("utf-8"))
        body.extend(b"\r\n")

    for field_name, file_name, content_type, file_bytes in form_files:
        safe_field = str(field_name).replace('"', "")
        safe_name = os.path.basename(str(file_name) or "upload.bin").replace('"', "")
        safe_content_type = content_type or "application/octet-stream"

        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="{safe_field}"; filename="{safe_name}"\r\n'.encode("utf-8")
        )
        body.extend(f"Content-Type: {safe_content_type}\r\n\r\n".encode("utf-8"))
        body.extend(file_bytes)
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    content_type = f"multipart/form-data; boundary={boundary}"
    return bytes(body), content_type


def submit_aws_batch_job(notebook, final_payload, uploaded_files):
    fields = []
    for key, val in final_payload.items():
        if key.startswith("_download_"):
            continue
        if key == "execution_profile":
            continue
        fields.append((key, str(val)))
    fields.append(("execution_profile", "ec2_200gb"))

    files = []
    notebook_name = os.path.basename(notebook.notebook_file.name) or "notebook.ipynb"
    with notebook.notebook_file.open("rb") as notebook_file:
        files.append(("notebook", notebook_name, "application/x-ipynb+json", notebook_file.read()))

    if "environment" in uploaded_files:
        env_file = uploaded_files["environment"]
        env_file.seek(0)
        files.append((
            "environment",
            os.path.basename(env_file.name) or "environment.yaml",
            env_file.content_type or "application/x-yaml",
            env_file.read(),
        ))
    elif notebook.environment_file:
        with notebook.environment_file.open("rb") as env_file:
            files.append((
                "environment",
                os.path.basename(notebook.environment_file.name) or "environment.yaml",
                "application/x-yaml",
                env_file.read(),
            ))

    for key, file_list in uploaded_files.lists():
        if key == "environment":
            continue
        for uploaded_file in file_list:
            uploaded_file.seek(0)
            files.append((
                key,
                os.path.basename(uploaded_file.name),
                uploaded_file.content_type or "application/octet-stream",
                uploaded_file.read(),
            ))

    body_bytes, content_type = _build_multipart_body(fields, files)
    event = {
        "headers": {"content-type": content_type},
        "body": base64.b64encode(body_bytes).decode("utf-8"),
        "isBase64Encoded": True,
    }

    lambda_client_kwargs = {"region_name": settings.AWS_BATCH_TRIGGER_REGION}

    trigger_access_key = getattr(settings, "AWS_BATCH_TRIGGER_ACCESS_KEY_ID", None)
    trigger_secret_key = getattr(settings, "AWS_BATCH_TRIGGER_SECRET_ACCESS_KEY", None)
    trigger_session_token = getattr(settings, "AWS_BATCH_TRIGGER_SESSION_TOKEN", None)

    if trigger_access_key and trigger_secret_key:
        lambda_client_kwargs["aws_access_key_id"] = trigger_access_key
        lambda_client_kwargs["aws_secret_access_key"] = trigger_secret_key
        if trigger_session_token:
            lambda_client_kwargs["aws_session_token"] = trigger_session_token
    else:
        # Local docker defaults use MinIO credentials that are invalid for real AWS APIs.
        if (
            os.getenv("ENVIRONMENT", "").lower() == "local"
            and os.getenv("AWS_ACCESS_KEY_ID") == "admin"
            and os.getenv("AWS_SECRET_ACCESS_KEY") == "password123"
        ):
            raise RuntimeError(
                "AWS batch trigger credentials are missing. Set "
                "AWS_BATCH_TRIGGER_ACCESS_KEY_ID and AWS_BATCH_TRIGGER_SECRET_ACCESS_KEY "
                "(and AWS_BATCH_TRIGGER_SESSION_TOKEN if using temporary credentials)."
            )

    lambda_client = boto3.client("lambda", **lambda_client_kwargs)
    invoke_response = lambda_client.invoke(
        FunctionName=settings.AWS_BATCH_TRIGGER_FUNCTION,
        InvocationType="RequestResponse",
        Payload=json.dumps(event).encode("utf-8"),
    )

    payload_bytes = invoke_response["Payload"].read()
    payload_json = json.loads(payload_bytes.decode("utf-8")) if payload_bytes else {}

    if invoke_response.get("FunctionError"):
        raise RuntimeError(payload_json)

    status_code = payload_json.get("statusCode", 500)
    body = payload_json.get("body")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            body = {"raw_body": body}
    elif body is None:
        body = {}

    if status_code >= 400:
        raise RuntimeError(body.get("error") or f"Batch trigger returned status {status_code}")

    batch_job_id = body.get("batch_job_id")
    if not batch_job_id:
        raise RuntimeError("Batch trigger response missing batch_job_id")

    return body


class NotebookViewSet(viewsets.ModelViewSet):
    """
    Provides GET /api/notebooks/, POST /api/notebooks/ (Upload), 
    GET /api/notebooks/<id>/, and DELETE /api/notebooks/<id>/
    """
    serializer_class = NotebookSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notebook.objects.filter(owner=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        notebook_file = self.request.FILES.get('notebook_file')
        extracted_params = parse_notebook_parameters(notebook_file) if notebook_file else []
        serializer.save(owner=self.request.user, parameter_schema=extracted_params)

    @extend_schema(
        summary="Trigger Notebook Job",
        description="Executes a notebook by queuing it to Kubernetes. Accepts dynamic multipart/form-data for parameters and files based on the notebook's extracted schema.",
        request={'multipart/form-data': OpenApiTypes.OBJECT},
        responses={
            202: inline_serializer(
                name='JobTriggerResponse',
                fields={
                    'message': serializers.CharField(),
                    'job_id': serializers.UUIDField(),
                    'status': serializers.CharField(),
                    'execution_profile': serializers.CharField(),
                    'resolved_payload': serializers.DictField()
                }
            ),
            500: inline_serializer(
                name='JobTriggerError',
                fields={'error': serializers.CharField()}
            )
        }
    )
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        notebook = self.get_object()
        
        try:
            raw_execution_profile = request.data.get("execution_profile") or request.data.get("compute_profile")
            execution_profile = normalize_execution_profile(raw_execution_profile)
            if not execution_profile:
                return Response(
                    {"error": "Invalid execution_profile. Allowed values: standard, ec2_200gb"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            schema_data = notebook.parameter_schema
            param_list = [item for item in schema_data if isinstance(item, dict)]
            final_payload = parse_notebook_parameters_from_payload(param_list, request.data.items(), request.FILES)
            final_payload["execution_profile"] = execution_profile

            for key, uploaded_file in request.FILES.items():
                original_filename = os.path.basename(uploaded_file.name)
                saved_path = default_storage.save(f"api_uploads/{uploaded_file.name}", uploaded_file)
                raw_url = default_storage.url(saved_path)
                file_url = get_safe_url(raw_url)
                
                final_payload[f"_download_{key}"] = file_url
                if execution_profile == "ec2_200gb":
                    # AWS Batch worker downloads uploaded files using the original multipart filename.
                    final_payload[key] = original_filename
                else:
                    final_payload[key] = os.path.basename(saved_path)
            batch_submit_result = None
            initial_status = "PENDING"

            if execution_profile == "ec2_200gb":
                try:
                    batch_submit_result = submit_aws_batch_job(notebook, final_payload, request.FILES)
                    final_payload["batch_job_id"] = batch_submit_result.get("batch_job_id")
                    final_payload["batch_submission_job_id"] = batch_submit_result.get("job_id")
                    initial_status = "PROVISIONING"
                except Exception as exc:
                    return Response(
                        {"error": f"AWS Batch submission failed: {str(exc)}"},
                        status=status.HTTP_502_BAD_GATEWAY,
                    )

            job = Job.objects.create(
                user=request.user,
                notebook=notebook,
                status=initial_status,
                job_parameters=final_payload
            )

            if execution_profile != "ec2_200gb":
                transaction.on_commit(lambda: dispatch_job_task.delay(job.id))

            response_payload = {
                "message": "Job successfully queued.",
                "job_id": str(job.id),
                "status": job.status,
                "execution_profile": execution_profile,
                "resolved_payload": final_payload
            }
            if batch_submit_result:
                response_payload["batch_job_id"] = batch_submit_result.get("batch_job_id")

            return Response(response_payload, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response({"error": f"Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
