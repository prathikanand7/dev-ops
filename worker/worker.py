"""Batch worker entrypoint.

This script is executed inside the worker container by AWS Batch. It pulls job
inputs from S3, creates a conda environment from the
uploaded environment file, executes the notebook with Papermill, and uploads
the produced artefacts back to S3.
"""

import os
import sys
import subprocess
import shutil
import boto3
import json
import papermill as pm
import botocore


def download_s3_folder(s3_client, bucket, prefix, local_dir="."):
    """Downloads all files from a specific S3 prefix to a local directory."""
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            s3_key = obj["Key"]
            filename = os.path.basename(s3_key)

            # Skip empty directory markers
            if not filename:
                continue

            local_path = os.path.join(local_dir, filename)
            print(f"Downloading s3://{bucket}/{s3_key} to {local_path}...")
            s3_client.download_file(bucket, s3_key, local_path)


def zip_and_upload_folder(
    s3_client, bucket, prefix, local_dir="./outputs", zip_filename="outputs"
):
    """Zips a local directory and uploads it to S3 as a single archive."""
    if not os.path.exists(local_dir) or not os.listdir(local_dir):
        print(f"Directory {local_dir} does not exist or is empty. Skipping upload.")
        return

    print(f"Zipping {local_dir} into {zip_filename}.zip...")
    # shutil.make_archive creates the zip file in the current working directory
    shutil.make_archive(zip_filename, "zip", local_dir)

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

# Handle Dynamic Environment (Download from Root Level)
env_file_path = None
try:
    s3.download_file(bucket, f"{prefix}environment.yaml", "./environment.yaml")
    env_file_path = "./environment.yaml"
except botocore.exceptions.ClientError as e:
    if e.response["Error"]["Code"] == "404":
        try:
            s3.download_file(bucket, f"{prefix}environment.yml", "./environment.yml")
            env_file_path = "./environment.yml"
        except botocore.exceptions.ClientError as e2:
            if e2.response["Error"]["Code"] == "404":
                print("No environment file (.yaml or .yml) found at job root.")
            else:
                print(f"FATAL: Error checking for environment.yml: {e2}")
                sys.exit(1)
    else:
        print(f"FATAL: Error checking for environment.yaml: {e}")
        sys.exit(1)

# Download the Input files
try:
    print("Downloading input files...")
    download_s3_folder(s3, bucket, f"{prefix}inputs/")
except Exception as e:
    print(f"FATAL: Failed to download input files: {e}")
    sys.exit(1)

# Determine notebook language
try:
    with open(input_nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)
    lang = nb_data.get("metadata", {}).get("language_info", {}).get("name", "r").lower()
    auto_kernel = "python3" if lang == "python" else "ir"
except Exception:
    print("Warning: Could not detect notebook language, defaulting to 'python3'.")
    lang = "python"
    auto_kernel = "python3"

# Build Isolated Sandbox if Environment File Exists
if env_file_path and os.path.exists(env_file_path):
    print(
        f"Environment file ({env_file_path}) detected! Building isolated sandbox environment..."
    )
    try:
        # Create new environment named 'job_env'
        subprocess.run(
            ["mamba", "env", "create", "-n", "job_env", "-f", env_file_path], check=True
        )

        # Inject kernel into isolated environment
        if lang == "python":
            subprocess.run(
                ["mamba", "install", "-n", "job_env", "ipykernel", "-y"], check=True
            )
            subprocess.run(
                [
                    "conda",
                    "run",
                    "-n",
                    "job_env",
                    "python",
                    "-m",
                    "ipykernel",
                    "install",
                    "--user",
                    "--name",
                    "job_env",
                ],
                check=True,
            )
        else:
            subprocess.run(
                ["mamba", "install", "-n", "job_env", "r-irkernel", "-y"], check=True
            )
            subprocess.run(
                [
                    "conda",
                    "run",
                    "-n",
                    "job_env",
                    "Rscript",
                    "-e",
                    "IRkernel::installspec(name='job_env', user=TRUE)",
                ],
                check=True,
            )

        # Override the Papermill kernel
        auto_kernel = "job_env"
        print(f"Isolated sandbox built and registered as kernel: {auto_kernel}")

    except subprocess.CalledProcessError as e:
        print(
            f"FATAL: Failed to build isolated environment. Error code: {e.returncode}"
        )
        sys.exit(1)
else:
    print("Using default container tools (No custom environment built).")

# Execute Notebook via Papermill
output_nb_path = "output.ipynb"
try:
    print(f"Executing notebook using kernel: {auto_kernel}...")
    pm.execute_notebook(
        input_nb_path, output_nb_path, kernel_name=auto_kernel, log_output=True
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
