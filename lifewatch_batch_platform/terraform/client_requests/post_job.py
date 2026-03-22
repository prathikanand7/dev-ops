"""Manual client script for POST /batch/jobs.

This is used to create jobs manually. Use the returned Job ID as input for the other manual scripts.
"""

import requests
from fetch_api_key import fetch_api_key
from fetch_api_url import fetch_api_url

API_URL = fetch_api_url().rstrip("/") + "/batch/jobs"
API_KEY = fetch_api_key()

NOTEBOOK_PATH = "../../../demo_input/Data_cleaning.ipynb"
DATA_FILE_PATH = "../../../demo_input/Template_MBO_Example_raw_v3.xlsx"
ENV_FILE_PATH = "../../../demo_input/environment.yaml"
EXECUTION_PROFILE = "standard"  # Allowed: "standard", "ec2_200gb"

print(f"Sending {NOTEBOOK_PATH} and {DATA_FILE_PATH} to AWS...")
print(f"Execution profile: {EXECUTION_PROFILE}")

headers = {"x-api-key": API_KEY, "Accept": "multipart/form-data"}

with (
    open(NOTEBOOK_PATH, "rb") as nb_file,
    open(DATA_FILE_PATH, "rb") as data_file,
    open(ENV_FILE_PATH, "rb") as env_file,
):
    files = {
        "notebook": (NOTEBOOK_PATH, nb_file.read(), "application/x-ipynb+json"),
        "upload_01": (
            DATA_FILE_PATH,
            data_file.read(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        "environment": (ENV_FILE_PATH, env_file.read(), "application/x-yaml"),
        # R parameters
        "param_01_input_data_filename": (None, "Template_MBO_Example_raw_v3.xlsx"),
        "param_02_input_data_sheet": (None, "BIRDS"),
        "param_03_input_metadata_sheet": (None, "METADATA"),
        "param_04_output_samples_ecological_parameters": (None, "false"),
        "param_05_output_make_plots": (None, "true"),
        "param_07_first_month": (None, "1"),
        "param_10_upper_limit_max_depth": (None, "1"),
        "execution_profile": (None, EXECUTION_PROFILE),
    }

    try:
        response = requests.post(API_URL, files=files, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        print("\n=== CLOUD RESPONSE ===")
        print(f"Status Code: {response.status_code}")
        print(
            f"Response:{response_json.get('message', response_json.get('text', 'No message available'))}"
        )
        job_id = response_json.get("job_id")
        print("======================")
        if job_id:
            print("Job ID:", job_id)
    except requests.HTTPError as e:
        print(f"HTTP error: {e}")
        if "response" in locals() and hasattr(response, "text"):
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Failed to post job: {e}")
