import json
import boto3
import uuid
import os
import base64
import re
from email.parser import BytesParser
from email.policy import default

s3 = boto3.client("s3")
batch = boto3.client("batch")

BUCKET = os.environ["BUCKET"]
STANDARD_JOB_QUEUE = os.environ.get("STANDARD_JOB_QUEUE") or os.environ.get("JOB_QUEUE")
STANDARD_JOB_DEFINITION = os.environ.get("STANDARD_JOB_DEFINITION") or os.environ.get("JOB_DEFINITION")
EC2_200GB_JOB_QUEUE = os.environ.get("EC2_200GB_JOB_QUEUE")
EC2_200GB_JOB_DEFINITION = os.environ.get("EC2_200GB_JOB_DEFINITION")

PROFILE_ALIASES = {
    "standard": "standard",
    "fargate": "standard",
    "default": "standard",
    "ec2_200gb": "ec2_200gb",
    "ec2-200gb": "ec2_200gb",
    "ec2_200": "ec2_200gb",
    "high-storage": "ec2_200gb"
}


def normalize_execution_profile(raw_profile):
    normalized_key = (raw_profile or "standard").strip().lower()
    return PROFILE_ALIASES.get(normalized_key)


def resolve_batch_target(execution_profile):
    if execution_profile == "standard":
        if not STANDARD_JOB_QUEUE or not STANDARD_JOB_DEFINITION:
            raise RuntimeError("Missing STANDARD_JOB_QUEUE or STANDARD_JOB_DEFINITION configuration.")
        return STANDARD_JOB_QUEUE, STANDARD_JOB_DEFINITION

    if execution_profile == "ec2_200gb":
        if not EC2_200GB_JOB_QUEUE or not EC2_200GB_JOB_DEFINITION:
            raise RuntimeError("Missing EC2_200GB_JOB_QUEUE or EC2_200GB_JOB_DEFINITION configuration.")
        return EC2_200GB_JOB_QUEUE, EC2_200GB_JOB_DEFINITION

    raise ValueError(f"Unsupported execution profile: {execution_profile}")

def lambda_handler(event, context):
    try:
        # Initialize Job Context
        job_id = str(uuid.uuid4())
        s3_prefix = f"jobs/{job_id}/"
        
        # Extract and decode the request body (API Gateway handling)
        content_type = event.get("headers", {}).get("content-type") or event.get("headers", {}).get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            return {"statusCode": 400, "body": "Request must be multipart/form-data"}

        raw_body = event.get("body", "")
        body_bytes = base64.b64decode(raw_body) if event.get("isBase64Encoded") else raw_body.encode("utf-8")

        # Use Python's built-in email parser to parse multipart data (no external libraries needed)
        headers_and_body = f"Content-Type: {content_type}\r\n\r\n".encode("utf-8") + body_bytes
        msg = BytesParser(policy=default).parsebytes(headers_and_body)

        notebook_content = None
        environment_content = None
        params = {}
        files_to_upload = []

        # Categorize the multipart form parts
        for part in msg.iter_parts():
            field_name = part.get_param("name", header="content-disposition")
            filename = part.get_filename()
            payload = part.get_payload(decode=True)

            if field_name == "notebook":
                notebook_content = payload
            elif field_name == "environment":
                environment_content = payload
            elif filename:
                # Clean relative paths from filename
                safe_filename = os.path.basename(filename)
                files_to_upload.append({"filename": safe_filename, "content": payload})
            elif field_name:
                # If no filename, treat it as a parameter key-value pair
                params[field_name] = payload.decode("utf-8")

        raw_execution_profile = params.get("execution_profile") or params.get("compute_profile")
        execution_profile = normalize_execution_profile(raw_execution_profile)
        if not execution_profile:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Invalid execution_profile. Allowed values: standard, ec2_200gb"
                })
            }

        selected_job_queue, selected_job_definition = resolve_batch_target(execution_profile)

        if not notebook_content:
            return {"statusCode": 400, "body": "Missing mandatory 'notebook' file."}

        notebook_json = json.loads(notebook_content.decode("utf-8"))
        
        # Format the parameters for R syntax
        formatted_params = {}
        for key, val in params.items():
            if key.startswith("param_"):
                # Basic type inference: keep digits as numbers, wrap everything else in quotes
                if val.replace(".", "", 1).isdigit():
                    formatted_params[key] = f'{key} <- {val}\n'
                else:
                    formatted_params[key] = f'{key} <- "{val}"\n'

        # Inject LifeWatch configuration overrides to ensure the notebook runs inside the Batch container
        # TODO: Verify this
        formatted_params.update({
            "conf_temporary_data_directory": 'conf_temporary_data_directory <- "./outputs"\n',
            "conf_virtual_lab_biotisan_euromarec": 'conf_virtual_lab_biotisan_euromarec <- "vl-biotisan-euromarec"\n',
            "conf_naavre_public": 'conf_naavre_public <- "naa-vre-public"\n',
            "conf_naavre_user_data": 'conf_naavre_user_data <- ""\n',
            "conf_cloud_storage_path": 'conf_cloud_storage_path <- "."\n'
        })

        # Loop through all cells and substitute the existing lines
        for cell in notebook_json.get("cells", []):
            if cell.get("cell_type") == "code":
                new_source = []
                for line in cell.get("source", []):
                    replaced = False
                    # Check if this line assigns a value to one of our parameters or config variables
                    for param_key, param_line in formatted_params.items():
                        # Matches the variable name, optional spaces, and the <- operator
                        if re.match(rf"^{re.escape(param_key)}\s*<-", line):
                            new_source.append(param_line)
                            replaced = True
                            break # Move to the next line in the cell once replaced
                    
                    # If it's not a parameter or config line, keep the original line
                    if not replaced:
                        new_source.append(line)
                        
                # Update the cell's source code
                cell["source"] = new_source

        updated_notebook_bytes = json.dumps(notebook_json).encode("utf-8")

        # Upload Artifacts to S3
        s3.put_object(Bucket=BUCKET, Key=f"{s3_prefix}notebook.ipynb", Body=updated_notebook_bytes)
        
        if environment_content:
            s3.put_object(Bucket=BUCKET, Key=f"{s3_prefix}environment.yaml", Body=environment_content)
            
        for f in files_to_upload:
            s3.put_object(Bucket=BUCKET, Key=f"{s3_prefix}inputs/{f['filename']}", Body=f["content"])

        # Submit the Batch Job
        response = batch.submit_job(
            jobName=f"r-notebook-job-{job_id[:8]}",
            jobQueue=selected_job_queue,
            jobDefinition=selected_job_definition,
            containerOverrides={
                "environment": [
                    # Pass the S3 location so the worker knows where to pull from
                    {"name": "JOB_ID", "value": job_id},
                    {"name": "S3_JOB_PREFIX", "value": f"s3://{BUCKET}/{s3_prefix}"}
                ]
            }
        )

        # Tracking file in S3 links the custom job_id to the AWS Batch ID
        meta_payload = {
            "batch_job_id": response["jobId"],
            "execution_profile": execution_profile
        }
        s3.put_object(
            Bucket=BUCKET,
            Key=f"{s3_prefix}meta.json",
            Body=json.dumps(meta_payload).encode("utf-8")
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Job successfully mapped and submitted",
                "job_id": job_id,
                "execution_profile": execution_profile
            })
        }

    except Exception as e:
        import traceback
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "trace": traceback.format_exc()})
        }
