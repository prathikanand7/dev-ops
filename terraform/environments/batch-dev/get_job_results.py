import requests
import sys

API_BASE_URL = "https://wd2iz3j4nl.execute-api.eu-west-1.amazonaws.com/dev"
API_KEY = ""

if len(sys.argv) != 2:
    print("Usage: python get_job_results.py <job_id>")
    sys.exit(1)

job_id = sys.argv[1]

url = f"{API_BASE_URL}/batch/jobs/{job_id}/results"
headers = {"x-api-key": API_KEY}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    download_url = data.get("download_url")

    if not download_url:
        print(f"Error: No download URL found in response. Response: {data}")
        sys.exit(1)

    print(f"Result S3 URL: {download_url}")

except requests.HTTPError as e:
    print(f"HTTP error: {e}")
    if 'response' in locals() and hasattr(response, 'text'):
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")