import os
import time
import requests
# REPLACE THESE WITH YOUR VALUES
NOTEBOOK_ID = <NOTEBOOK_ID>
TOKEN = <TOKEN>
BASE_URL = <BASE_URL>

headers = {
    "Authorization": f"Token {TOKEN}"
}

data_payload = {
    "param_09_years": 5
}

with open('./Template_MBO_Example_raw_v3.xlsx', 'rb') as upload_file:
    files_payload = {
        "param_01_input_data_filename": upload_file
    }
    print(f"Submitting job to {BASE_URL}...")
    response = requests.post(BASE_URL, data=data_payload, files=files_payload, headers=headers)

print(f"Status Code: {response.status_code}")
if response.status_code == 202:
    print("Success! Server Response:")
    response_data = response.json()
    print(response_data)
    
    job_id = response_data.get("job_id")
    status_url = f"{BASE_URL}/api/jobs/{job_id}/status/"
    
    print(f"\nPolling for job completion...")
    
    while True:
        status_response = requests.get(status_url, headers=headers)
        
        if status_response.status_code != 200:
            print(f"Error checking status: {status_response.text}")
            break
            
        status_data = status_response.json()
        current_status = status_data.get("status")
        
        print(f"   Current Status: {current_status}...")
        
        if current_status == "SUCCESS":
            print("\nJob finished successfully!")
            download_url = status_data.get("download_url")
            
            if download_url:
                print(f"Downloading results from {download_url}...")
                file_resp = requests.get(download_url, headers=headers)
                
                if file_resp.status_code == 200:
                    output_filename = f"results_{job_id}.zip"
                    with open(output_filename, 'wb') as f:
                        f.write(file_resp.content)
                    print(f"Successfully saved results to {os.path.abspath(output_filename)}")
                else:
                    print(f"Failed to download file. Status code: {file_resp.status_code}")
            else:
                print("No download URL provided in the response.")
            break
            
        elif current_status in ["FAILED", "ERROR"]:
            print("\nJob failed.")
            print("Logs:\n", status_data.get("logs", "No logs provided."))
            break
            
        time.sleep(5)

else:
    print("Failed. Server Response:")
    print(response.text)