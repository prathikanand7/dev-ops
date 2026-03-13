import requests
import sys
from fetch_api_key import fetch_api_key

API_BASE_URL = "https://n69rb6bzvl.execute-api.eu-west-1.amazonaws.com/dev"
API_KEY = fetch_api_key()

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