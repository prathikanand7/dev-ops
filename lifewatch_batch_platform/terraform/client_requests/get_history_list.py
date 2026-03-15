import requests
import json
from fetch_api_key import fetch_api_key
from fetch_api_url import fetch_api_url

API_URL = fetch_api_url().rstrip("/") + "/batch/jobs/history_list"
API_KEY = fetch_api_key()

print(f"Fetching job history from AWS...")
print(f"Endpoint: {API_URL}")

headers = {
    "x-api-key": API_KEY,
    "Accept": "application/json"
}

try:
    response = requests.get(API_URL, headers=headers)
    response.raise_for_status()
    response_json = response.json()
    print(response_json)  # Debug: Print the full response JSON
    
    print("\n=== CLOUD RESPONSE ===")
    print(f"Status Code: {response.status_code}")
    print("======================\n")
    
    jobs = response_json.get("jobs", [])
    
    if not jobs:
        print("No jobs found in history.")
    else:
        print(f"Found {len(jobs)} jobs:\n")
        for i, job in enumerate(jobs, 1):
            print(f"{i}. Job ID: {job.get('job_id')}")
            print(f"   Batch ID: {job.get('batch_job_id', 'unknown')}")
            print(f"   Profile:  {job.get('execution_profile', 'unknown')}")
            print("-" * 40)

except requests.HTTPError as e:
    print(f"HTTP error: {e}")
    if hasattr(e, 'response') and hasattr(e.response, 'text'):
        print(f"Response: {e.response.text}")
except Exception as e:
    print(f"Failed to fetch job history: {e}")