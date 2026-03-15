import json
import boto3
import os
from handle_cors import response as cors_response

s3 = boto3.client("s3")
batch = boto3.client("batch")
BUCKET = os.environ["BUCKET"]

def lambda_handler(event, context):
    try:
        paginator = s3.get_paginator('list_objects_v2')
        jobs_history = []
        batch_job_ids = []  # IDs used to query Batch
        
        for page in paginator.paginate(Bucket=BUCKET, Prefix="jobs/", Delimiter="/"):
            for prefix in page.get('CommonPrefixes', []):
                job_folder = prefix.get('Prefix')
                job_id = job_folder.split('/')[1]
                
                job_data = {
                    "job_id": job_id,
                    "execution_profile": "unknown",
                    "batch_job_id": "unknown",
                    "created_at": None,
                    "status": "UNKNOWN"
                }
                
                # Fetch the meta.json
                try:
                    meta_obj = s3.get_object(Bucket=BUCKET, Key=f"{job_folder}meta.json")
                    
                    # Extract Creation Date from S3 metadata
                    last_modified = meta_obj['LastModified']
                    job_data['created_at'] = last_modified.isoformat()
                    
                    meta_content = json.loads(meta_obj['Body'].read().decode('utf-8'))
                    job_data.update(meta_content)
                    
                    # Store the batch ID to query later
                    if job_data.get("batch_job_id") != "unknown":
                        batch_job_ids.append(job_data["batch_job_id"])
                        
                except s3.exceptions.NoSuchKey:
                    pass # Skip if meta.json is missing
                
                jobs_history.append(job_data)
        
        # Fetch Status from AWS Batch
        if batch_job_ids:
            status_map = {}
            for i in range(0, len(batch_job_ids), 100):
                chunk = batch_job_ids[i:i + 100]
                batch_response = batch.describe_jobs(jobs=chunk)
                
                for job in batch_response.get('jobs', []):
                    status_map[job['jobId']] = job['status']
            
            for job in jobs_history:
                if job['batch_job_id'] in status_map:
                    job['status'] = status_map[job['batch_job_id']]

        jobs_history.sort(
            key=lambda x: x.get('created_at') or "1970-01-01T00:00:00+00:00", 
            reverse=True
        )

        return cors_response(200, {"jobs": jobs_history})

    except Exception as e:
        import traceback
        return cors_response(500, {"error": str(e), "trace": traceback.format_exc()})