import os
import sys
import subprocess
import shutil
import boto3
import botocore
import papermill as pm

def download_s3_folder(s3_client, bucket, prefix, local_dir="."):
    """Downloads all files from a specific S3 prefix to a local directory."""
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            s3_key = obj['Key']
            filename = os.path.basename(s3_key)
            
            # Skip empty directory markers
            if not filename:
                continue
                
            local_path = os.path.join(local_dir, filename)
            print(f"Downloading s3://{bucket}/{s3_key} to {local_path}...")
            s3_client.download_file(bucket, s3_key, local_path)

def zip_and_upload_folder(s3_client, bucket, prefix, local_dir="./outputs", zip_filename="outputs"):
    """Zips a local directory and uploads it to S3 as a single archive."""
    if not os.path.exists(local_dir) or not os.listdir(local_dir):
        print(f"Directory {local_dir} does not exist or is empty. Skipping upload.")
        return

    print(f"Zipping {local_dir} into {zip_filename}.zip...")
    # shutil.make_archive creates the zip file in the current working directory
    shutil.make_archive(zip_filename, 'zip', local_dir)
    
    zip_path = f"{zip_filename}.zip"
    s3_key = f"{prefix}{zip_path}"
    
    print(f"Uploading {zip_path} to s3://{bucket}/{s3_key}...")
    s3_client.upload_file(zip_path, bucket, s3_key)

# Initialization and Environment Variable Checks
s3 = boto3.client("s3")

job_id = os.environ.get("JOB_ID")
s3_job_prefix_uri = os.environ.get("S3_JOB_PREFIX")

if not job_id or not s3_job_prefix_uri:
    print("FATAL: JOB_ID and S3_JOB_PREFIX environment variables must be set.")
    sys.exit(1)

# Parse the S3 URI
# s3_job_prefix_uri.split("/") -> ['s3:', '', 'my-bucket', 'jobs', 'uuid', '']
bucket = s3_job_prefix_uri.split("/")[2]
prefix = "/".join(s3_job_prefix_uri.split("/")[3:])

print(f"Starting Job: {job_id}")
print(f"Target Bucket: {bucket} | Prefix: {prefix}")

# Download the Notebook
input_nb_path = "notebook.ipynb"
try:
    print("Downloading notebook...")
    s3.download_file(bucket, f"{prefix}notebook.ipynb", input_nb_path)
except Exception as e:
    print(f"FATAL: Failed to download notebook from S3: {e}")
    sys.exit(1)

# Download the Inputs (Excel files, CSVs, etc.)
try:
    print("Downloading input files...")
    download_s3_folder(s3, bucket, f"{prefix}inputs/")
except Exception as e:
    print(f"FATAL: Failed to download input files: {e}")
    sys.exit(1)

# Handle Dynamic Environment (Mamba)
env_file_path = "environment.yaml"
try:
    # Attempt to download the environment file. If it doesn't exist, just skip.
    s3.download_file(bucket, f"{prefix}environment.yaml", env_file_path)
    
    print("Environment file detected. Installing dynamic dependencies via mamba...")
    try:
        subprocess.run(
            ["mamba", "env", "update", "--name", "base", "--file", env_file_path],
            check=True,
            stdout=sys.stdout, 
            stderr=sys.stderr
        )
        print("Dynamic dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"FATAL: Failed to install dependencies. Error code: {e.returncode}")
        sys.exit(1)

except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == "404":
        print("No environment file provided. Using default container environment.")
    else:
        print(f"FATAL: Error checking for environment file: {e}")
        sys.exit(1)

# Execute Notebook via Papermill
output_nb_path = "output.ipynb"
try:
    print("Executing notebook via Papermill...")
    pm.execute_notebook(
        input_nb_path,
        output_nb_path,
        kernel_name='ir',
        log_output=True
    )
    print("Execution Successful!")
except pm.PapermillExecutionError as e:
    print(f"FATAL: Notebook Logic Error in cell {e.exec_count}: {e}")
    
    # Upload the partially executed notebook anyway for debugging
    s3.upload_file(output_nb_path, bucket, f"{prefix}failed_output.ipynb")
    # Attempt to zip and upload whatever outputs were generated before the crash
    zip_and_upload_folder(s3, bucket, prefix, "./outputs", "failed_outputs")
    sys.exit(1)
except Exception as e:
    print(f"FATAL: An unexpected error occurred during notebook execution: {e}")
    sys.exit(1)

# Upload the successful results back to S3
try:
    # Upload the fully executed notebook
    output_key = f"{prefix}output.ipynb"
    print(f"Uploading executed notebook to s3://{bucket}/{output_key}...")
    s3.upload_file(output_nb_path, bucket, output_key)
    
    # Zip and upload everything in the local ./outputs directory
    print("Zipping and uploading generated data files...")
    zip_and_upload_folder(s3, bucket, prefix, "./outputs", "outputs")
    
    print("Upload complete. Container exiting cleanly.")
except Exception as e:
    print(f"FATAL: Failed to upload outputs: {e}")
    sys.exit(1)

sys.exit(0)