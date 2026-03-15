import json
import boto3
import os
from handle_cors import response as cors_response

s3 = boto3.client("s3")
BUCKET = os.environ["BUCKET"]

def lambda_handler(event, context):
    try:
        paginator = s3.get_paginator('list_objects_v2')
        jobs_history = []
        
        for page in paginator.paginate(Bucket=BUCKET, Prefix="jobs/", Delimiter="/"):
            for prefix in page.get('CommonPrefixes', []):
                job_folder = prefix.get('Prefix')
                job_id = job_folder.split('/')[1]
                
                job_data = {
                    "job_id": job_id,
                    "execution_profile": "unknown",
                    "batch_job_id": "unknown"
                }
                
                # Fetch the meta.json for the history table details
                try:
                    meta_obj = s3.get_object(Bucket=BUCKET, Key=f"{job_folder}meta.json")
                    meta_content = json.loads(meta_obj['Body'].read().decode('utf-8'))
                    job_data.update(meta_content)
                except s3.exceptions.NoSuchKey:
                    pass # Skip if meta.json hasn't been written yet or is missing
                
                jobs_history.append(job_data)
        
        # Reverse the list so the newest jobs appear first
        jobs_history.reverse()

        return cors_response(200, {"jobs": jobs_history})

    except Exception as e:
        import traceback
        return cors_response(500, {"error": str(e), "trace": traceback.format_exc()})