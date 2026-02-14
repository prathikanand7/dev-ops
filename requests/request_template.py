import requests
# REPLACE THESE WITH YOUR VALUES
NOTEBOOK_ID = <NOTEBOOK_ID>
TOKEN = <TOKEN>

API_URL = f"http://127.0.0.1:8000/api/v1/notebooks/{NOTEBOOK_ID}/run/"

headers = {
    "Authorization": f"Token {TOKEN}"
}

data_payload = {
    "param_09_years": 5
}

files_payload = {
    "param_01_input_data_filename": open('./Template_MBO_Example_raw_v3.xlsx', 'rb')
}

print(f"Submitting job to {API_URL}...")

response = requests.post(API_URL, data=data_payload, files=files_payload, headers=headers)

print(f"Status Code: {response.status_code}")
if response.status_code == 202:
    print("Success! Server Response:")
    print(response.json())
else:
    print("Failed. Server Response:")
    print(response.text)