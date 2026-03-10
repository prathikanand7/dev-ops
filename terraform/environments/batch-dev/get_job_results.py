import os
import json
import base64
import requests
import sys

API_BASE_URL = "https://wd2iz3j4nl.execute-api.eu-west-1.amazonaws.com/dev"
API_KEY = ""

if len(sys.argv) != 3:
    print("Usage: python get_job_results.py <job_id> <output_dir>")
    sys.exit(1)

job_id = sys.argv[1]
output_dir = sys.argv[2]

os.makedirs(output_dir, exist_ok=True)

url = f"{API_BASE_URL}/batch/jobs/{job_id}/results"
headers = {"x-api-key": API_KEY}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])

    for file_entry in results:
        filename = file_entry["filename"]
        content_b64 = file_entry["content_base64"]
        content_bytes = base64.b64decode(content_b64)

        file_path = os.path.join(output_dir, filename)
        with open(file_path, "wb") as f:
            f.write(content_bytes)

        print(f"Wrote {filename} to {file_path}")

except requests.HTTPError as e:
    print(f"HTTP error: {e} | Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")