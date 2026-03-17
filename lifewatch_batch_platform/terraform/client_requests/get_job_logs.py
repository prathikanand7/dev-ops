"""Manual client script for GET /batch/jobs/{job_id}/logs."""

import requests
import sys
from fetch_api_key import fetch_api_key
from fetch_api_url import fetch_api_url

API_BASE_URL = fetch_api_url()
API_KEY = fetch_api_key()

if len(sys.argv) != 2:
    print("Usage: python get_job_logs.py <job_id>")
    sys.exit(1)

job_id = sys.argv[1]

url = f"{API_BASE_URL}/batch/jobs/{job_id}/logs"

headers = {
    "x-api-key": API_KEY
}

try:
    response = requests.get(url, headers=headers)

    print("\n=== JOB LOGS ===")
    print(f"Status Code: {response.status_code}")
    print(response.text)

except Exception as e:
    print(f"Request failed: {e}")
