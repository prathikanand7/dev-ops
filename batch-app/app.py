import boto3
import json
import os

s3 = boto3.client("s3")

bucket = os.environ["BUCKET"]
key = os.environ["KEY"]

# Download file
response = s3.get_object(Bucket=bucket, Key=key)
content = response["Body"].read().decode("utf-8")

# Parse JSON safely
try:
    data = json.loads(content)
except json.JSONDecodeError:
    print("Input is not valid JSON. Treating as plain text.")
    data = {"content": content}

# Add hello world message
data["message"] = "hello world"

# Upload updated JSON back
s3.put_object(
    Bucket=bucket,
    Key=key,
    Body=json.dumps(data).encode("utf-8")
)

print("File processed successfully")