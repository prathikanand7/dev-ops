## Notebook Jobs Frontend (Serverless)

React + TypeScript frontend that talks directly to AWS API Gateway + Lambda + AWS Batch.


### What this frontend does

- Submits notebook jobs with multipart payloads to Lambda (`POST /batch/jobs`)
- Polls AWS Batch status via Lambda (`GET /batch/jobs/{job_id}`)
- Fetches logs (`GET /batch/jobs/{job_id}/logs`)
- Fetches output artifacts (`GET /batch/jobs/{job_id}/results`)
- Downloads result files in browser from Base64 payloads
- Parses notebook parameters in-browser using the native `FileReader` API

### Native FileReader parameter extraction

When a user drops an `.ipynb` file:

1. `FileReader.readAsText(...)` reads notebook JSON in browser memory.
2. The app parses the `cells` array.
3. It locates the code cell tagged with `metadata.tags` containing `parameters`.
4. It extracts assignment lines using both `=` and `<-` patterns.
5. It normalizes primitive values (number, boolean, string) and writes strict JSON into the parameters editor.

This avoids any backend endpoint for notebook parameter extraction.

### Getting started

From repo root:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Quick workflow

1. Enter API Gateway base URL (for example: `https://<api-id>.execute-api.eu-west-1.amazonaws.com/dev`).
2. Paste API key (sent as `x-api-key`).
3. Drop one notebook `.ipynb` file and optional data files (`.xlsx`/`.xls`).
4. Verify or edit extracted parameters JSON.
5. Select `execution_profile` and submit.
6. Monitor status, then fetch logs and results.

### API contract used by frontend

All requests include:

```http
x-api-key: <your_api_key>
```

Routes:

- `POST /batch/jobs`
- `GET /batch/jobs/{job_id}`
- `GET /batch/jobs/{job_id}/logs`
- `GET /batch/jobs/{job_id}/results`

Submit payload (`multipart/form-data`) includes:

- `notebook`: notebook file (`.ipynb`) [required]
- `execution_profile`: `standard` or `ec2_200gb`
- `param_*`: scalar parameters as plain form fields
- additional files as form-data file parts

### Expected backend responses

`POST /batch/jobs`:

```json
{
  "message": "Job successfully mapped and submitted",
  "job_id": "...",
  "batch_job_id": "...",
  "execution_profile": "standard"
}
```

`GET /batch/jobs/{job_id}`:

```json
{
  "job_id": "...",
  "job_name": "...",
  "status": "SUBMITTED"
}
```

`GET /batch/jobs/{job_id}/logs`:

```json
{
  "job_id": "...",
  "logs": ["line1", "line2"]
}
```

`GET /batch/jobs/{job_id}/results`:

```json
{
  "job_id": "...",
  "results": [
    {
      "filename": "result.csv",
      "content_base64": "..."
    }
  ]
}
```

### Reliability notes

- Polling auto-stops on terminal statuses: `SUCCEEDED`, `FAILED`.
- API Gateway often returns `body` as a JSON string in Lambda proxy mode; frontend safely decodes both object and string bodies.
- Parameter extraction failures do not block submission; users can still edit JSON manually.
- On the backend side, ensure CORS is configured for browser clients (`OPTIONS` + `Access-Control-Allow-*` headers).

### Test file

Use `frontend/test.http` to validate the serverless endpoints.

### Stack

- React 18 + TypeScript
- Vite
- Bootstrap 5 (CSS)
- `react-dropzone`
