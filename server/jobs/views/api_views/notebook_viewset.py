import os
from django.core.files.storage import default_storage
from django.db import transaction
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
from jobs.utils import parse_notebook_parameters, parse_notebook_parameters_from_payload

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
                saved_path = default_storage.save(f"api_uploads/{uploaded_file.name}", uploaded_file)
                raw_url = default_storage.url(saved_path)
                file_url = get_safe_url(raw_url)
                
                final_payload[f"_download_{key}"] = file_url
                final_payload[key] = os.path.basename(saved_path)
            
            job = Job.objects.create(
                user=request.user,
                notebook=notebook,
                status='PENDING',
                job_parameters=final_payload
            )

            transaction.on_commit(lambda: dispatch_job_task.delay(job.id))

            return Response({
                "message": "Job successfully queued.",
                "job_id": str(job.id),
                "status": "PENDING",
                "execution_profile": execution_profile,
                "resolved_payload": final_payload 
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response({"error": f"Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
