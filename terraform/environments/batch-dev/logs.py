import boto3
import json

logs_client = boto3.client("logs")
batch_client = boto3.client("batch")

# AWS Batch default log group
LOG_GROUP = "/aws/batch/job"

def lambda_handler(event, context):
    """
    Returns CloudWatch logs for a Batch job.
    Expects: path parameter 'job_id'
    """
    try:
        job_id = event.get("pathParameters", {}).get("job_id")
        if not job_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing path parameter 'job_id'"})
            }

        # Get the job description
        response = batch_client.describe_jobs(jobs=[job_id])
        if not response["jobs"]:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Job not found"})
            }

        job = response["jobs"][0]

        # Log stream name inside CloudWatch
        log_stream = job.get("container", {}).get("logStreamName")
        if not log_stream:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Log stream not found for job"})
            }

        # Fetch log events
        log_events = logs_client.get_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=log_stream,
            startFromHead=True
        )

        messages = [e["message"] for e in log_events.get("events", [])]

        return {
            "statusCode": 200,
            "body": json.dumps({"job_id": job_id, "logs": messages})
        }

    except Exception as e:
        import traceback
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "trace": traceback.format_exc()})
        }