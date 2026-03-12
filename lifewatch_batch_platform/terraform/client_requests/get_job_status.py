import requests
import sys

API_BASE_URL = "https://wd2iz3j4nl.execute-api.eu-west-1.amazonaws.com/dev"
API_KEY = ""

if len(sys.argv) != 2:
    print("Usage: python get_job_status.py <job_id>")
    sys.exit(1)

job_id = sys.argv[1]

url = f"{API_BASE_URL}/batch/jobs/{job_id}"

headers = {
    "x-api-key": API_KEY
}

try:
    response = requests.get(url, headers=headers)

    print("\n=== JOB STATUS ===")
    print(f"Status Code: {response.status_code}")
    print(response.text)

except Exception as e:
    print(f"Request failed: {e}")