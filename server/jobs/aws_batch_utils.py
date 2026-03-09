"""
AWS Batch Integration Utilities
Provides functions to submit jobs to AWS Batch and retrieve job status/logs.
"""
import os
import boto3
from botocore.exceptions import ClientError
from django.conf import settings


def get_batch_client():
    """
    Returns an authenticated AWS Batch client.
    Uses environment variables for credentials and region configuration.
    """
    region = os.getenv('AWS_BATCH_REGION', os.getenv('AWS_S3_REGION_NAME', 'us-east-1'))
    
    return boto3.client(
        'batch',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )


def get_logs_client():
    """
    Returns an authenticated CloudWatch Logs client for retrieving job logs.
    """
    region = os.getenv('AWS_BATCH_REGION', os.getenv('AWS_S3_REGION_NAME', 'us-east-1'))
    
    return boto3.client(
        'logs',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )


def submit_batch_job(job_name, job_queue, job_definition, parameters=None, environment=None):
    """
    Submits a job to AWS Batch.
    
    Args:
        job_name (str): Unique name for the job
        job_queue (str): Name or ARN of the job queue
        job_definition (str): Name or ARN of the job definition
        parameters (dict): Optional container overrides parameters
        environment (list): Optional environment variables as list of dicts with 'name' and 'value' keys
        
    Returns:
        dict: Response from AWS Batch containing jobId, jobName, etc.
        
    Raises:
        ClientError: If submission fails
    """
    batch_client = get_batch_client()
    
    submit_job_kwargs = {
        'jobName': job_name,
        'jobQueue': job_queue,
        'jobDefinition': job_definition,
    }
    
    if parameters:
        submit_job_kwargs['parameters'] = parameters
    
    container_overrides = {}
    if environment:
        container_overrides['environment'] = environment
    
    if container_overrides:
        submit_job_kwargs['containerOverrides'] = container_overrides
    
    try:
        response = batch_client.submit_job(**submit_job_kwargs)
        return response
    except ClientError as e:
        raise Exception(f"Failed to submit batch job: {e}")


def get_batch_job_status(job_id):
    """
    Retrieves the current status of an AWS Batch job.
    
    Args:
        job_id (str): The AWS Batch job ID
        
    Returns:
        dict: Job details including status, statusReason, createdAt, startedAt, stoppedAt, etc.
        Status can be: SUBMITTED, PENDING, RUNNABLE, STARTING, RUNNING, SUCCEEDED, or FAILED
        
    Raises:
        Exception: If job is not found or API call fails
    """
    batch_client = get_batch_client()
    
    try:
        response = batch_client.describe_jobs(jobs=[job_id])
        
        if not response.get('jobs'):
            raise Exception(f"Job {job_id} not found")
        
        job = response['jobs'][0]
        return {
            'jobId': job.get('jobId'),
            'jobName': job.get('jobName'),
            'status': job.get('status'),
            'statusReason': job.get('statusReason', ''),
            'createdAt': job.get('createdAt'),
            'startedAt': job.get('startedAt'),
            'stoppedAt': job.get('stoppedAt'),
            'logStreamName': job.get('container', {}).get('logStreamName'),
        }
    except ClientError as e:
        raise Exception(f"Failed to get job status: {e}")


def get_batch_job_logs(log_stream_name, log_group_name=None, max_lines=1000):
    """
    Retrieves CloudWatch logs for an AWS Batch job.
    
    Args:
        log_stream_name (str): The CloudWatch log stream name (from job description)
        log_group_name (str): The CloudWatch log group name (defaults to /aws/batch/job)
        max_lines (int): Maximum number of log lines to retrieve
        
    Returns:
        str: Concatenated log messages
        
    Raises:
        Exception: If logs cannot be retrieved
    """
    if not log_stream_name:
        return "Log stream not available yet. Job may not have started."
    
    if log_group_name is None:
        log_group_name = '/aws/batch/job'
    
    logs_client = get_logs_client()
    
    try:
        response = logs_client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name,
            limit=max_lines,
            startFromHead=True
        )
        
        events = response.get('events', [])
        if not events:
            return "No logs available yet."
        
        log_messages = [event.get('message', '') for event in events]
        return '\n'.join(log_messages)
    
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            return "Log stream not found. Job may not have started yet."
        raise Exception(f"Failed to retrieve logs: {e}")


def terminate_batch_job(job_id, reason="Job termination requested by user"):
    """
    Terminates a running AWS Batch job.
    
    Args:
        job_id (str): The AWS Batch job ID
        reason (str): Reason for termination
        
    Returns:
        dict: Response from AWS Batch
        
    Raises:
        Exception: If termination fails
    """
    batch_client = get_batch_client()
    
    try:
        response = batch_client.terminate_job(
            jobId=job_id,
            reason=reason
        )
        return response
    except ClientError as e:
        raise Exception(f"Failed to terminate job: {e}")
