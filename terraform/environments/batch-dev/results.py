import os
import json
import boto3
import base64

s3 = boto3.client("s3")
BUCKET = os.environ["BUCKET"]  # e.g., lifewatch-batch-payloads-020858641931

def lambda_handler(event, context):
    """
    Returns /output folter of a Batch job.
    Expects: path parameter 'job_id'
    """
    try:
        job_id = event.get("pathParameters", {}).get("job_id")
        if not job_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing path parameter 'job_id'"})
            }

        print("job_id was found in param")

        prefix = f"jobs/{job_id}/outputs/"
        objects = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)

        if "Contents" not in objects:
            return {"statusCode": 404, "body": json.dumps({"error": f"No outputs found for job {job_id}"})}
        
        print("job_id made it after contents")

        results = []
        for obj in objects["Contents"]:
            key = obj["Key"]
            # Skip folders
            if key.endswith("/"):
                continue

            file_obj = s3.get_object(Bucket=BUCKET, Key=key)
            content_bytes = file_obj["Body"].read()
            # Encode files in Base64 so they can be safely returned in JSON
            content_b64 = base64.b64encode(content_bytes).decode("utf-8")

            results.append({
                "filename": key.replace(prefix, ""),  # just the file name
                "content_base64": content_b64
            })

        return {
            "statusCode": 200,
            "body": json.dumps({
                "job_id": job_id,
                "results": results
            })
        }

    except Exception as e:
        import traceback
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "trace": traceback.format_exc()
            })
        }