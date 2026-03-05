import yaml
import nbformat
import papermill as pm
import os
import sys
import json
import subprocess
import boto3
import base64

def fetch_bucket(s3_objects):
    for obj in s3_objects:
        obj_bucket = obj["bucket"]
        obj_key = obj["key"]

        filename = os.path.basename(obj_key)
        local_path = os.path.join(".", filename)

        print(f"Downloading s3://{obj_bucket}/{obj_key}")

        s3.download_file(
            obj_bucket,
            obj_key,
            local_path
        )

def extract_excel_files(input_files):
    for input_file in input_files:
        file_name = input_file.get("name")
        b64_data = input_file.get("data")

        if not file_name or not b64_data:
            print(f"Warning: Missing 'name' or 'data' for an Excel file. Skipping...")
            continue

        print(f"Decoding and writing {file_name} to local storage...")
        
        file_bytes = base64.b64decode(b64_data)
        with open(file_name, "wb") as f:
            f.write(file_bytes)


# Initialize S3 client
s3 = boto3.client("s3")

# Passed via ECS Container Overrides
bucket = os.environ.get("BUCKET")
key = os.environ.get("KEY")

if not bucket or not key:
    print("FATAL: BUCKET and KEY environment variables must be set.")
    sys.exit(1)

# 1. Download the main payload file
print(f"Downloading payload from s3://{bucket}/{key}...")
try:
    response = s3.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read().decode("utf-8")
except Exception as e:
    print(f"FATAL: Failed to download payload from S3: {e}")
    sys.exit(1)

# 2. Parse JSON safely
try:
    data = json.loads(content)
except json.JSONDecodeError:
    print("FATAL: Input is not valid JSON. Cannot proceed.")
    sys.exit(1)

s3_objects = data.get("s3_compatible_storage_objects", [])
excel_files = data.get("excel_inputs", [])
outputs = data.get("outputs", [])
parameters = data.get("parameters", {})
notebook = data.get("notebook", {})
environment = data.get("environment", {})

fetch_bucket(s3_objects)
extract_excel_files(excel_files)

# 4. Parse and write notebook to a physical file for Papermill
input_nb_path = "input.ipynb"
try:
    nb = nbformat.from_dict(notebook)
    with open(input_nb_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
except Exception as e:
    print(f"FATAL: Failed to parse or write notebook JSON: {e}")
    sys.exit(1)

# 5. Handle dynamic environment (Mamba)
if environment:
    env_yaml_string = yaml.dump(environment, default_flow_style=False)
    print("Environment dict detected. Installing dynamic dependencies...")
    try:
        subprocess.run(
            ["mamba", "env", "update", "--name", "base", "--file", "-"],
            input=env_yaml_string,  
            text=True,
            check=True,
            stdout=sys.stdout, 
            stderr=sys.stderr
        )
        print("Dynamic dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"FATAL: Failed to install dependencies. Error code: {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"FATAL: An unexpected error occurred during dependency installation: {e}")
        sys.exit(1)

# 6. Execute Notebook
output_nb_path = "output.ipynb"
try:
    print("Executing notebook via Papermill...")
    pm.execute_notebook(
        input_nb_path,
        output_nb_path,
        parameters=parameters,
        kernel_name='ir',
        log_output=True
    )
    print("Execution Successful!")
except pm.PapermillExecutionError as e:
    print(f"FATAL: Notebook Logic Error in cell {e.exec_count}: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FATAL: An unexpected error occurred during notebook execution: {e}")
    sys.exit(1)

# 7. Upload the results back to S3
output_key = f"completed/{key}"
try:
    print(f"Uploading executed notebook to s3://{bucket}/{output_key}...")
    s3.upload_file(output_nb_path, bucket, output_key)
    print("Upload complete. Container exiting cleanly.")
except Exception as e:
    print(f"FATAL: Failed to upload output notebook: {e}")
    sys.exit(1)

sys.exit(0)