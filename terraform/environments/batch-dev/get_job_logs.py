import requests
import sys

API_BASE_URL = "https://5xnkmozte8.execute-api.eu-west-1.amazonaws.com/dev"
API_KEY = "<copy the api key from AWS>"

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