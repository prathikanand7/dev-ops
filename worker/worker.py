import papermill as pm
import os
import sys
import json
import requests
import subprocess

# Constants
BASE_DIR = "/app"
INPUT_DIR = os.path.join(BASE_DIR, "inputs")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_file(url, dest_folder):
    local_filename = os.path.join(dest_folder, url.split('/')[-1])
    print(f"Downloading: {url} -> {local_filename}")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename
    except Exception as e:
        print(f"FATAL: Download failed: {e}")
        sys.exit(1)

# Get env variables
env_params_str = os.environ.get("JOB_PARAMETERS")
if not env_params_str:
    print("FATAL: No 'JOB_PARAMETERS' environment variable found.")
    sys.exit(1)

try:
    user_parameters = json.loads(env_params_str)
    print("Loaded parameters from environment.")
except json.JSONDecodeError as e:
    print(f"FATAL: Could not decode JOB_PARAMETERS JSON: {e}")
    sys.exit(1)

# Get notebook
notebook_url = user_parameters.pop("_notebook_url", None)
notebook_filename = user_parameters.pop("_notebook_filename", None)
job_id = user_parameters.pop("_job_id", None)     
base_url = user_parameters.pop("_base_url", None) 

def report_status_to_django(status, log_message, file_path=None):
    """Report job status back to Django backend.
    """
    if not job_id or not base_url:
        print("Warning: No _job_id or _base_url provided. Cannot report status.")
        return
        
    webhook_url = f"{base_url}/api/jobs/{job_id}/complete/"
    data = {"status": status, "logs": log_message}
    files = {}
    
    if file_path and os.path.exists(file_path):
        files = {'output_file': open(file_path, 'rb')}
        
    try:
        print(f"Sending status '{status}' to {webhook_url}...")
        response = requests.post(webhook_url, data=data, files=files)
        response.raise_for_status()
        print("Status reported successfully.")
    except Exception as e:
        print(f"Failed to report status to Django: {e}")

if notebook_url:
    input_nb_path = download_file(notebook_url, INPUT_DIR)
    notebook_filename = os.path.basename(input_nb_path)
elif notebook_filename:
    input_nb_path = os.path.join(INPUT_DIR, notebook_filename)
else:
    print("FATAL: No '_notebook_url' or '_notebook_filename' provided.")
    sys.exit(1)

output_nb_path = os.path.join(OUTPUT_DIR, "result_" + notebook_filename)

# Download possible input files
download_keys = [k for k in user_parameters.keys() if k.startswith("_download_")]

for d_key in download_keys:
    file_url = user_parameters.pop(d_key)
    print(f"Found dynamic dataset requirement: {d_key}")
    download_file(file_url, INPUT_DIR)

# Install packages
env_url = user_parameters.pop("_environment_url", None)
if env_url:
    print(f"Environment file detected. Downloading from {env_url}...")
    env_path = download_file(env_url, INPUT_DIR)
    
    print("Installing dynamic dependencies... (This may take a minute)")
    try:
        subprocess.run(
            ["mamba", "env", "update", "--name", "base", "--file", env_path],
            check=True,
            stdout=sys.stdout, 
            stderr=sys.stderr
        )
        print("Dynamic dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"FATAL: Failed to install dependencies. Error code: {e.returncode}")
        report_status_to_django('FAILED', f"Dependency Installation Failed: {e}")
        sys.exit(1)

# System Config
system_config = {
    "conf_cloud_storage_path": INPUT_DIR,
    "conf_temporary_data_directory": OUTPUT_DIR
}
final_parameters = {**user_parameters, **system_config}

print(f"Starting Execution: {notebook_filename}")

# Execute
try:
    pm.execute_notebook(
        input_nb_path,
        output_nb_path,
        parameters=final_parameters,
        kernel_name='ir',
        log_output=True,
        cwd=INPUT_DIR
    )
    print("Execution Successful")
    report_status_to_django('SUCCESS', 'Execution completed successfully.', output_nb_path)
    
except pm.PapermillExecutionError as e:
    error_msg = f"Notebook Logic Error in cell {e.exec_count}: {e}"
    print(f"{error_msg}")
    report_status_to_django('FAILED', error_msg)
    sys.exit(1)
except Exception as e:
    error_msg = f"System Error: {e}"
    print(f"{error_msg}")
    report_status_to_django('FAILED', error_msg)
    sys.exit(1)