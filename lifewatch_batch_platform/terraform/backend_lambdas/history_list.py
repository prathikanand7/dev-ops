"""Lambda handler for GET /batch/jobs/history_list.

Combine metadata from S3 and the logs from AWS Batch
"""

import json
import boto3
import os
from datetime import datetime, timezone
from handle_cors import response as cors_response

s3 = boto3.client("s3")
batch = boto3.client("batch")
BUCKET = os.environ["BUCKET"]


def lambda_handler(event, context):
    try:
        paginator = s3.get_paginator("list_objects_v2")
        jobs_history = []
        job_map = {}

        # Fetch metadata from S3
        for page in paginator.paginate(Bucket=BUCKET, Prefix="jobs/", Delimiter="/"):
            for prefix in page.get("CommonPrefixes", []):
                job_folder = prefix.get("Prefix")
                job_id = job_folder.split("/")[1]

                # Base object mirrors JobHistoryItem interface for frontend
                ts_item = {
                    "jobId": job_id,
                    "submittedAt": "",
                    "notebookName": "Unknown",
                    "environmentName": "Unknown",
                    "executionProfile": "unknown",
                    "params": {},
                    "status": "UNKNOWN",
                    "logs": "",  # Fetch separately in frontend
                    "artifactUrl": None,  # Fetch separately in frontend
                    "s3Uri": f"s3://{BUCKET}/{job_folder}",
                    "info": None,
                    "error": None,
                    "lastCheckedAt": datetime.now(timezone.utc).isoformat(),
                }

                try:
                    meta_obj = s3.get_object(
                        Bucket=BUCKET, Key=f"{job_folder}meta.json"
                    )

                    # Extract timestamp from S3 metadata
                    ts_item["submittedAt"] = meta_obj["LastModified"].isoformat()
                    meta_content = json.loads(meta_obj["Body"].read().decode("utf-8"))
                    ts_item["executionProfile"] = meta_content.get(
                        "execution_profile", "unknown"
                    )
                    ts_item["notebookName"] = meta_content.get(
                        "notebook_name", "notebook.ipynb"
                    )
                    ts_item["environmentName"] = meta_content.get(
                        "environment_name", "environment.yaml"
                    )
                    ts_item["params"] = meta_content.get("params", {})

                    batch_id = meta_content.get("batch_job_id")
                    if batch_id:
                        job_map[batch_id] = ts_item

                except s3.exceptions.NoSuchKey:
                    pass  # Skip if the JSON is missing

                jobs_history.append(ts_item)

        # Fetch Status from Batch
        batch_ids = list(job_map.keys())
        if batch_ids:
            # describe_jobs has a limit of 100 jobs
            for i in range(0, len(batch_ids), 100):
                chunk = batch_ids[i : i + 100]
                batch_response = batch.describe_jobs(jobs=chunk)

                for job in batch_response.get("jobs", []):
                    b_id = job["jobId"]
                    status = job["status"]
                    reason = job.get("statusReason", "")

                    # Update the object in place
                    mapped_item = job_map[b_id]
                    mapped_item["status"] = status

                    if status == "FAILED":
                        mapped_item["error"] = reason
                    elif reason:
                        mapped_item["info"] = reason

        # Sort Chronologically
        jobs_history.sort(
            key=lambda x: x.get("submittedAt") or "1970-01-01T00:00:00+00:00",
            reverse=True,
        )

        return cors_response(200, {"jobs": jobs_history})

    except Exception as e:
        import traceback

        return cors_response(500, {"error": str(e), "trace": traceback.format_exc()})
