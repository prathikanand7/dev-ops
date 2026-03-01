import json
import boto3
import uuid
import os

s3 = boto3.client("s3")
batch = boto3.client("batch")

BUCKET = os.environ["BUCKET"]
JOB_QUEUE = os.environ["JOB_QUEUE"]
JOB_DEFINITION = os.environ["JOB_DEFINITION"]

def lambda_handler(event, context):
    body = event["body"]
    key = f"{uuid.uuid4()}.txt"

    # Save request body to S3
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=body.encode("utf-8")
    )

    # Submit Batch job
    batch.submit_job(
        jobName="hello-world-job",
        jobQueue=JOB_QUEUE,
        jobDefinition=JOB_DEFINITION,
        containerOverrides={
            "environment": [
                {"name": "KEY", "value": key}
            ]
        }
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Job submitted", "key": key})
    }