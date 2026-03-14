import boto3
import json
import os
from handle_cors import response as cors_response

logs_client = boto3.client("logs")
batch_client = boto3.client("batch")
s3 = boto3.client("s3")

LOG_GROUP = "/aws/batch/job"
BUCKET = os.environ["BUCKET"]

def lambda_handler(event, context):
    """
    Returns CloudWatch logs for a Batch job.
    Expects: path parameter 'job_id'
    """
    try:
        job_id = event.get("pathParameters", {}).get("job_id")
        if not job_id:
            return cors_response(400, {"error": "Missing path parameter 'job_id'"})

        # Translate job_id to AWS Batch ID using S3
        try:
            meta_obj = s3.get_object(Bucket=BUCKET, Key=f"jobs/{job_id}/meta.json")
            meta = json.loads(meta_obj["Body"].read().decode("utf-8"))
            batch_job_id = meta["batch_job_id"]
        except s3.exceptions.NoSuchKey:
            return cors_response(404, {"error": f"Job metadata not found for job_id: {job_id}"})

        # Get the job description
        response = batch_client.describe_jobs(jobs=[batch_job_id])
        if not response["jobs"]:
            return cors_response(404, {"error": "Batch Job not found in AWS"})

        job = response["jobs"][0]

        # Get log stream name inside CloudWatch
        log_stream = job.get("container", {}).get("logStreamName")
        if not log_stream:
            return cors_response(404, {"error": "Log stream not found for job"})

        # Fetch log events
        log_events = logs_client.get_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=log_stream,
            startFromHead=True
        )

        messages = [e["message"] for e in log_events.get("events", [])]

        return cors_response(200, {"job_id": job_id, "logs": messages})

    except Exception as e:
        import traceback
        return cors_response(500, {"error": str(e), "trace": traceback.format_exc()})
