import papermill as pm
import os
import sys
import json

# Constants
BASE_DIR = "/app"
INPUT_DIR = os.path.join(BASE_DIR, "inputs")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# Get Env Variables
env_params_str = os.environ.get("JOB_PARAMETERS")

if not env_params_str:
    print("FATAL: No 'JOB_PARAMETERS' environment variable found.")
    print("   Usage: docker run -e JOB_PARAMETERS='{...}' ...")
    sys.exit(1)

try:
    # Parse the JSON string back into a Python Dictionary
    user_parameters = json.loads(env_params_str)
    print("Loaded parameters from environment.")
except json.JSONDecodeError as e:
    print(f"FATAL: Could not decode JOB_PARAMETERS JSON: {e}")
    sys.exit(1)

# Get Notebook
notebook_filename = user_parameters.pop("_notebook_filename", None)

if not notebook_filename:
    # If not provided, try to find the only .ipynb file in inputs
    try:
        notebooks = [f for f in os.listdir(INPUT_DIR) if f.endswith('.ipynb')]
    except FileNotFoundError:
        print(f"FATAL: Input directory {INPUT_DIR} does not exist.")
        sys.exit(1)

    if len(notebooks) == 1:
        notebook_filename = notebooks[0]
        print(f"Auto-detected notebook: {notebook_filename}")
    else:
        print("FATAL: You must specify '_notebook_filename' in JOB_PARAMETERS or have exactly one .ipynb in inputs.")
        sys.exit(1)

input_nb_path = os.path.join(INPUT_DIR, notebook_filename)
output_nb_path = os.path.join(OUTPUT_DIR, "result_" + notebook_filename)

# --- Input/Output Config
system_config = {
    "conf_cloud_storage_path": INPUT_DIR,
    "conf_temporary_data_directory": OUTPUT_DIR
}

final_parameters = {**user_parameters, **system_config}

print(f"Starting Execution: {notebook_filename}")
print(f"Inputs: {INPUT_DIR}")
print(f"Outputs: {OUTPUT_DIR}")

# Execution
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
except pm.PapermillExecutionError as e:
    print(f"Notebook Logic Error in cell {e.exec_count}: {e}")
except Exception as e:
    print(f"System Error: {e}")
    sys.exit(1)