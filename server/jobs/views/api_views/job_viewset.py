from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from drf_spectacular.utils import extend_schema, inline_serializer

from jobs.serializers import JobSerializer
from jobs.models import Job
from .is_kubernetes_worker import IsKubernetesWorker

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