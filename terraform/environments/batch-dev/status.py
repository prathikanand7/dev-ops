import boto3
import json
import os

batch = boto3.client("batch")
s3 = boto3.client("s3")
BUCKET = os.environ["BUCKET"]

def lambda_handler(event, context):
    """
    Returns the status of a job.
    Expects: path parameter 'job_id'
    """
    try:
        # Get job_id from API Gateway path parameter
        job_id = event.get("pathParameters", {}).get("job_id")
        if not job_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing path parameter 'job_id'"})
            }

        # Translate job_id to AWS Batch ID using S3
        try:
            meta_obj = s3.get_object(Bucket=BUCKET, Key=f"jobs/{job_id}/meta.json")
            meta = json.loads(meta_obj["Body"].read().decode("utf-8"))
            batch_job_id = meta["batch_job_id"]
        except s3.exceptions.NoSuchKey:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": f"Job metadata not found for job_id: {job_id}"})
            }

        # Describe the job using the  Batch ID
        response = batch.describe_jobs(jobs=[batch_job_id])
        if not response["jobs"]:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Batch Job not found in AWS"})
            }

        job = response["jobs"][0]

        return {
            "statusCode": 200,
            "body": json.dumps({
                "job_id": job_id,
                "job_name": job.get("jobName"),
                "status": job.get("status"),
                "createdAt": job.get("createdAt"),
                "startedAt": job.get("startedAt"),
                "stoppedAt": job.get("stoppedAt"),
            })
        }

    except Exception as e:
        import traceback
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "trace": traceback.format_exc()})
        }