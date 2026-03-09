"""
AWS Batch API Views
Provides endpoints for submitting and monitoring AWS Batch jobs.
"""
import uuid
from django.conf import settings
from django.utils import timezone
from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from drf_spectacular.utils import extend_schema, inline_serializer
from drf_spectacular.types import OpenApiTypes

from jobs.models import Job, Notebook
from jobs.aws_batch_utils import submit_batch_job, get_batch_job_status, get_batch_job_logs


@extend_schema(
    summary="Submit AWS Batch Job",
    description="Submits a job to AWS Batch for notebook execution. Returns the job ID and initial status.",
    request={'multipart/form-data': OpenApiTypes.OBJECT},
    responses={
        202: inline_serializer(
            name='BatchJobSubmitResponse',
            fields={
                'message': serializers.CharField(),
                'job_id': serializers.UUIDField(),
                'aws_batch_job_id': serializers.CharField(),
                'status': serializers.CharField(),
                'resolved_payload': serializers.DictField()
            }
        ),
        400: inline_serializer(
            name='BatchJobSubmitError',
            fields={'error': serializers.CharField()}
        )
    }
)
@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def submit_notebook_to_batch(request, notebook_id):
    """
    Submit a notebook to AWS Batch for execution.
    
    This endpoint creates a Job record and submits it to AWS Batch.
    The job parameters are passed as environment variables to the Batch job.
    """
    try:
        notebook = Notebook.objects.get(id=notebook_id, owner=request.user)
    except Notebook.DoesNotExist:
        return Response(
            {"error": "Notebook not found or you don't have permission to access it."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check AWS Batch configuration
    if not settings.AWS_BATCH_JOB_QUEUE or not settings.AWS_BATCH_JOB_DEFINITION:
        return Response(
            {"error": "AWS Batch is not configured. Please set AWS_BATCH_JOB_QUEUE and AWS_BATCH_JOB_DEFINITION."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Parse parameters from request
    job_parameters = {}
    for key, value in request.data.items():
        if not key.startswith('_'):  # Skip internal parameters
            job_parameters[key] = str(value)
    
    # Handle file uploads
    for key, uploaded_file in request.FILES.items():
        # TODO: Upload files to S3 and add S3 URLs to parameters
        job_parameters[key] = uploaded_file.name
    
    # Create Job record in database
    job = Job.objects.create(
        user=request.user,
        notebook=notebook,
        status='PENDING',
        job_parameters=job_parameters,
        aws_batch_job_queue=settings.AWS_BATCH_JOB_QUEUE,
        aws_batch_job_definition=settings.AWS_BATCH_JOB_DEFINITION
    )
    
    # Prepare environment variables for Batch job
    environment_vars = [
        {'name': 'JOB_ID', 'value': str(job.id)},
        {'name': 'NOTEBOOK_ID', 'value': str(notebook.id)},
    ]
    
    # Add job parameters as environment variables
    for key, value in job_parameters.items():
        environment_vars.append({'name': key, 'value': str(value)})
    
    try:
        # Submit to AWS Batch
        batch_response = submit_batch_job(
            job_name=f"notebook-job-{job.id}",
            job_queue=settings.AWS_BATCH_JOB_QUEUE,
            job_definition=settings.AWS_BATCH_JOB_DEFINITION,
            environment=environment_vars
        )
        
        # Update job with AWS Batch job ID
        job.aws_batch_job_id = batch_response['jobId']
        job.status = 'SUBMITTED'
        job.save()
        
        return Response({
            "message": "Job successfully submitted to AWS Batch.",
            "job_id": str(job.id),
            "aws_batch_job_id": batch_response['jobId'],
            "status": "SUBMITTED",
            "resolved_payload": job_parameters
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        # Update job status to FAILED
        job.status = 'FAILED'
        job.logs = f"Failed to submit to AWS Batch: {str(e)}"
        job.save()
        
        return Response(
            {"error": f"Failed to submit job to AWS Batch: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Get AWS Batch Job Status",
    description="Retrieves the current status of an AWS Batch job. Status can be: SUBMITTED, PENDING, RUNNABLE, STARTING, RUNNING, SUCCEEDED, or FAILED.",
    responses={
        200: inline_serializer(
            name='BatchJobStatusResponse',
            fields={
                'job_id': serializers.UUIDField(),
                'aws_batch_job_id': serializers.CharField(),
                'status': serializers.CharField(),
                'status_reason': serializers.CharField(),
                'created_at': serializers.DateTimeField(),
                'started_at': serializers.IntegerField(required=False, allow_null=True),
                'stopped_at': serializers.IntegerField(required=False, allow_null=True),
            }
        ),
        404: inline_serializer(
            name='BatchJobStatusError',
            fields={'error': serializers.CharField()}
        )
    }
)
@api_view(['GET'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_job_status(request, job_id):
    """
    Get the current status of a job from AWS Batch.
    
    Updates the local Job record with the latest status from AWS Batch.
    """
    try:
        job = Job.objects.get(id=job_id, user=request.user)
    except Job.DoesNotExist:
        return Response(
            {"error": "Job not found or you don't have permission to access it."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if not job.aws_batch_job_id:
        # Return local status if it's not an AWS Batch job
        return Response({
            'job_id': str(job.id),
            'status': job.status,
            'logs': job.logs or "No logs available yet.",
        })
    
    try:
        # Get status from AWS Batch
        batch_status = get_batch_job_status(job.aws_batch_job_id)
        
        # Update local job record
        job.status = batch_status['status']
        
        # Update finished_at if job is complete
        if batch_status['status'] in ['SUCCEEDED', 'FAILED'] and batch_status.get('stoppedAt'):
            if not job.finished_at:
                job.finished_at = timezone.now()
        
        job.save()
        
        return Response({
            'job_id': str(job.id),
            'aws_batch_job_id': batch_status['jobId'],
            'status': batch_status['status'],
            'status_reason': batch_status.get('statusReason', ''),
            'created_at': job.created_at,
            'started_at': batch_status.get('startedAt'),
            'stopped_at': batch_status.get('stoppedAt'),
        })
        
    except Exception as e:
        return Response(
            {"error": f"Failed to get job status from AWS Batch: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Get AWS Batch Job Logs",
    description="Retrieves the CloudWatch logs for an AWS Batch job.",
    responses={
        200: inline_serializer(
            name='BatchJobLogsResponse',
            fields={
                'job_id': serializers.UUIDField(),
                'aws_batch_job_id': serializers.CharField(),
                'logs': serializers.CharField()
            }
        ),
        404: inline_serializer(
            name='BatchJobLogsError',
            fields={'error': serializers.CharField()}
        )
    }
)
@api_view(['GET'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_job_logs(request, job_id):
    """
    Get the CloudWatch logs for a job from AWS Batch.
    
    Returns the latest logs from CloudWatch Logs.
    """
    try:
        job = Job.objects.get(id=job_id, user=request.user)
    except Job.DoesNotExist:
        return Response(
            {"error": "Job not found or you don't have permission to access it."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if not job.aws_batch_job_id:
        # Return local logs if it's not an AWS Batch job
        return Response({
            'job_id': str(job.id),
            'logs': job.logs or "No logs available yet.",
        })
    
    try:
        # First get the job status to get the log stream name
        batch_status = get_batch_job_status(job.aws_batch_job_id)
        log_stream_name = batch_status.get('logStreamName')
        
        if not log_stream_name:
            return Response({
                'job_id': str(job.id),
                'aws_batch_job_id': job.aws_batch_job_id,
                'logs': 'Log stream not available yet. Job may not have started.'
            })
        
        # Get logs from CloudWatch
        logs = get_batch_job_logs(log_stream_name)
        
        # Update local job record with logs
        job.logs = logs
        job.save()
        
        return Response({
            'job_id': str(job.id),
            'aws_batch_job_id': job.aws_batch_job_id,
            'logs': logs
        })
        
    except Exception as e:
        return Response(
            {"error": f"Failed to get job logs from AWS Batch: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
