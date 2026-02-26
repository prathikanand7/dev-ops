import os
from django.core.files.storage import default_storage
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema, inline_serializer
from drf_spectacular.types import OpenApiTypes

from notebook_platform.settings import WORKER_CALLBACK_URL
from jobs.models import Job, Notebook
from jobs.serializers import NotebookSerializer, JobSerializer
from jobs.tasks import dispatch_job_task
from jobs.utils import parse_notebook_parameters, parse_notebook_parameters_from_payload

BASE_URL = WORKER_CALLBACK_URL.rstrip('/')

def get_safe_url(raw_url):
    if raw_url.startswith('http'):
        return raw_url
    if not raw_url.startswith('/'):
        raw_url = '/' + raw_url
    return f"{BASE_URL}{raw_url}"


class TokenStatusAPIView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Check API Token Status",
        description="Returns a boolean indicating if the current user has an active API token.",
        responses={
            200: inline_serializer(
                name='TokenStatusResponse',
                fields={'has_token': serializers.BooleanField()}
            )
        }
    )
    def get(self, request):
        has_token = Token.objects.filter(user=request.user).exists()
        return Response({'has_token': has_token})


class GenerateTokenAPIView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Generate API Token",
        description="Invalidates any existing token and generates a new one for the current user.",
        responses={
            201: inline_serializer(
                name='TokenGenerateResponse',
                fields={'token': serializers.CharField()}
            )
        }
    )
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        new_token = Token.objects.create(user=request.user)
        return Response({'token': new_token.key}, status=status.HTTP_201_CREATED)


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
            schema_data = notebook.parameter_schema
            param_list = [item for item in schema_data if isinstance(item, dict)]
            final_payload = parse_notebook_parameters_from_payload(param_list, request.data.items(), request.FILES)

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
                "resolved_payload": final_payload 
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response({"error": f"Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobViewSet(viewsets.ModelViewSet):
    """
    Provides GET /api/jobs/, GET /api/jobs/<id>/, DELETE /api/jobs/<id>/
    """
    serializer_class = JobSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Job.objects.filter(user=self.request.user).order_by('-created_at')

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
        return Response({'logs': job.logs or "No logs available yet..."})

    @extend_schema(
        summary="Job Complete Webhook",
        description="Unauthenticated webhook intended for the Kubernetes worker to post execution results.",
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
    @action(detail=True, methods=['post'], permission_classes=[AllowAny], authentication_classes=[])
    def complete(self, request, pk=None):
        job = get_object_or_404(Job, id=pk)
        
        job.status = request.data.get('status', 'SUCCESS')
        job.logs = request.data.get('logs', '')
        
        if 'output_file' in request.FILES:
            job.output_file = request.FILES['output_file']
            
        job.save()
        return Response({"message": f"Job {job.id} updated successfully."})