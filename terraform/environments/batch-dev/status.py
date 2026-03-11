import boto3
import json

batch = boto3.client("batch")

def lambda_handler(event, context):
    """
    Returns the status of a Batch job.
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

        # Describe the job
        response = batch.describe_jobs(jobs=[job_id])
        if not response["jobs"]:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Job not found"})
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