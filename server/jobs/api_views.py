import os
from django.core.files.storage import default_storage
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.authtoken.models import Token

from notebook_platform.settings import WORKER_CALLBACK_URL
from .models import Job, Notebook
from .serializers import NotebookSerializer, JobSerializer
from .tasks import dispatch_job_task
from .utils import parse_notebook_parameters, parse_notebook_parameters_from_payload

BASE_URL = WORKER_CALLBACK_URL.rstrip('/')

def get_safe_url(raw_url):
    if raw_url.startswith('http'):
        return raw_url
    if not raw_url.startswith('/'):
        raw_url = '/' + raw_url
    return f"{BASE_URL}{raw_url}"


class TokenStatusAPIView(APIView):
    """GET /api/token/status/"""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        has_token = Token.objects.filter(user=request.user).exists()
        return Response({'has_token': has_token})


class GenerateTokenAPIView(APIView):
    """POST /api/token/generate/"""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

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
        # Automatically assign the logged-in user and parse parameters on API upload
        notebook_file = self.request.FILES.get('notebook_file')
        extracted_params = parse_notebook_parameters(notebook_file) if notebook_file else []
        serializer.save(owner=self.request.user, parameter_schema=extracted_params)

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """POST /api/notebooks/<id>/run/"""
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

    # Disable creation of jobs directly via POST /api/jobs/ (must use notebook run action)
    def create(self, request, *args, **kwargs):
        return Response({"error": "Jobs must be created by triggering a notebook."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['get'])
    def poll_status(self, request):
        """GET /api/jobs/poll_status/ - Matches exact JSON format from previous poll_job_statuses"""
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

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """GET /api/jobs/<id>/logs/"""
        job = self.get_object()
        return Response({'logs': job.logs or "No logs available yet..."})

    @action(detail=True, methods=['post'], permission_classes=[AllowAny], authentication_classes=[])
    def complete(self, request, pk=None):
        """
        POST /api/jobs/<id>/complete/ 
        Webhook for K8s worker. Bypasses auth so the worker can hit it.
        """
        job = get_object_or_404(Job, id=pk)
        
        job.status = request.data.get('status', 'SUCCESS')
        job.logs = request.data.get('logs', '')
        
        if 'output_file' in request.FILES:
            job.output_file = request.FILES['output_file']
            
        job.save()
        return Response({"message": f"Job {job.id} updated successfully."})