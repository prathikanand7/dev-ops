# Notebook Jobs Frontend

React + TypeScript frontend for submitting notebook jobs to AWS API Gateway + Lambda + AWS Batch, monitoring active runs, and browsing historical runs.

## What This Frontend Does

- Submits notebook runs with multipart form data to `POST /batch/jobs`
- Checks run status with `GET /batch/jobs/{job_id}`
- Fetches logs from `GET /batch/jobs/{job_id}/logs`
- Fetches result ZIPs or inline result files from `GET /batch/jobs/{job_id}/results`
- Loads historical runs from `GET /batch/jobs/history_list`
- Parses notebook parameters in the browser from uploaded `.ipynb` files
- Supports dark/light theme switching in the UI

## Current Pages

### Job Submission

The Job Submission page is the operator workspace for launching and inspecting runs.

Features:

- Base URL input for the API Gateway endpoint
- API key input sent as the `x-api-key` header
- Controlled drag-and-drop upload area
- Required notebook file: `.ipynb`
- Required environment file: `.yaml`, `.yml`, or `.txt`
- Optional extra upload files such as `.xlsx` or `.xls`
- Automatic notebook parameter extraction from a tagged parameters cell
- `Edit Parameters` button opens a popup editor for extracted fields
- Popup parameter editor with inferred types: `string`, `number`, and `boolean`
- Execution profile selector driven by the shared backend profile catalog
- Per-profile compute details: backend type, vCPU, memory, and storage
- Indicative hourly cost estimate for the selected execution profile
- Submit button stays disabled until required inputs are present
- Job status panel for checking status, logs, and results after submission
- Automatic job ID handoff from the submission response into the status panel

### Job History

The Job History page is a condensed browser for previously submitted jobs.

Features:

- Refreshes cloud history from the backend `history_list` route
- Shows job ID, notebook name, status, created timestamp, and actions
- Lets users copy a job ID directly from the table
- Shows a brief confirmation toast when a job ID is copied
- Opens logs in a dedicated modal
- Opens captured run parameters in a dedicated modal
- Shows artifact download links for completed jobs when available
- Hydrates artifact links for successful jobs by checking the results endpoint
- Shows clear empty states when no API key is entered or no jobs are found

## UI Flow

```mermaid
flowchart TD
    A[User opens app] --> B[Enter base URL and API key]
    B --> C[Job Submission page]
    C --> D[Upload notebook and environment file]
    D --> E[Parse notebook parameters in browser]
    E --> F[Open Edit Parameters popup]
    F --> F1[Save and Close]
    F1 --> G[Submit job]
    G --> H[POST /batch/jobs]
    H --> I[Receive job_id]
    I --> J[Job Status panel]
    J --> K[GET /batch/jobs/{job_id}]
    J --> L[GET /batch/jobs/{job_id}/logs]
    J --> M[GET /batch/jobs/{job_id}/results]
    B --> N[Job History page]
    N --> O[GET /batch/jobs/history_list]
    O --> P[Open Logs modal]
    O --> Q[Open Params modal]
    O --> R[Open Artifacts link]
```

## File Structure

```text
frontend/
├── index.html
├── package.json
├── README.md
├── scripts/
│   └── generate-job-profiles.mjs
├── test.http
├── tsconfig.json
├── vite.config.ts
└── src/
    ├── App.tsx
    ├── main.tsx
    ├── styles.css
    ├── components/
    │   ├── DropZone.tsx
    │   ├── FilePreview.tsx
    │   ├── job_history/
    │   │   ├── JobHistoryTable.tsx
    │   │   ├── LogsModal.tsx
    │   │   └── ParamsModal.tsx
    │   └── job_submission/
    │       ├── ApiConnectionCard.tsx
    │       ├── JobStatusCard.tsx
    │       └── SubmitJobCard.tsx
    ├── config/
    │   ├── jobProfiles.generated.ts
    │   └── jobProfiles.ts
    ├── types/
    │   └── index.ts
    └── utils/
        ├── api.ts
        ├── notebook.ts
        └── storage.ts
```

## Folder Responsibilities

- `src/App.tsx`: top-level page composition, shared state, API orchestration, modal state, and page switching
- `src/components/job_submission/`: presentational UI for connection, submission, and live job monitoring
- `src/components/job_history/`: presentational UI for historical job browsing and modal views
- `src/components/DropZone.tsx`: controlled file upload/drop area
- `src/components/FilePreview.tsx`: upload file preview rendering
- `scripts/generate-job-profiles.mjs`: reads the root `job_profiles.json` and generates frontend profile config before dev/build/lint
- `src/config/jobProfiles.generated.ts`: generated execution profile data file, derived from the backend profile catalog
- `src/config/jobProfiles.ts`: stable wrapper exposing helpers around the generated execution profile data
- `src/types/index.ts`: shared frontend TypeScript types
- `src/utils/api.ts`: API response decoding and S3 URL helpers
- `src/utils/notebook.ts`: notebook parsing, file reading, and result download helpers
- `src/utils/storage.ts`: local storage helpers, history normalization, and upload file classification helpers
- `src/styles.css`: global visual styling and component/page styles

## Parameter Extraction

When a user drops an `.ipynb` file, the frontend reads it in browser memory using `FileReader`, parses the notebook JSON, finds the tagged parameters code cell, and converts assignment lines into typed form fields.

Supported behavior:

- Looks for a code cell tagged with `metadata.tags` including `parameters`
- Falls back to matching parameter-style assignments when no tagged cell is found
- Accepts both `=` and `<-` assignment styles
- Infers primitive values as `number`, `boolean`, or `string`
- Leaves submission usable even if extraction fails

## API Contract Used By The Frontend

All requests include:

```http
x-api-key: <your_api_key>
```

Routes currently used:

- `POST /batch/jobs`
- `GET /batch/jobs/{job_id}`
- `GET /batch/jobs/{job_id}/logs`
- `GET /batch/jobs/{job_id}/results`
- `GET /batch/jobs/history_list`

### Submit Request Shape

The submission request is `multipart/form-data` and includes:

- `notebook`: uploaded notebook file
- `environment`: uploaded environment file
- `execution_profile`: selected backend profile key, for example `standard` or `ec2_200gb`
- extracted parameter fields as plain scalar form values
- optional additional upload files

### Response Shapes

`POST /batch/jobs`

```json
{
  "message": "Job successfully mapped and submitted",
  "job_id": "...",
  "execution_profile": "standard"
}
```

`GET /batch/jobs/{job_id}`

```json
{
  "job_id": "...",
  "job_name": "...",
  "status": "SUBMITTED"
}
```

`GET /batch/jobs/{job_id}/logs`

```json
{
  "job_id": "...",
  "logs": ["line1", "line2"]
}
```

`GET /batch/jobs/{job_id}/results`

```json
{
  "job_id": "...",
  "download_url": "...",
  "results": [
    {
      "filename": "result.csv",
      "content_base64": "..."
    }
  ]
}
```

`GET /batch/jobs/history_list`

```json
{
  "jobs": [
    {
      "jobId": "...",
      "submittedAt": "...",
      "notebookName": "...",
      "environmentName": "...",
      "executionProfile": "standard",
      "params": {
        "param_name": "value"
      },
      "status": "SUCCEEDED",
      "logs": "",
      "artifactUrl": null,
      "s3Uri": null,
      "info": null,
      "error": null,
      "lastCheckedAt": null
    }
  ]
}
```

## Reliability Notes

- Polling stops automatically on terminal statuses: `SUCCEEDED` and `FAILED`
- Results are auto-fetched after a job transitions to `SUCCEEDED`
- API bodies are safely decoded whether Lambda returns a raw object or a stringified `body`
- History artifacts are hydrated separately so successful runs can expose ZIP links after list load
- Missing or delayed log streams are surfaced as user-facing info instead of breaking the page
- Parameter extraction failure does not block submission if the required files are present
- Cost estimates are indicative hourly estimates only; total cost depends on actual runtime
- Execution profile metadata is generated from the repository root `job_profiles.json` during `dev`, `build`, and `lint`

## Getting Started

From the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Quick Workflow

1. Enter the API Gateway base URL.
2. Paste the API key.
3. Upload one notebook and one environment file.
4. Review and edit extracted parameters.
5. Choose an execution profile.
6. Submit the job.
7. Track the run in the Job Status panel.
8. Browse previous runs in the Job History page.

## Test File

Use `frontend/test.http` to validate the serverless routes manually.

## Stack

- React 18
- TypeScript
- Vite
- react-dropzone
- react-icons
- Custom CSS in `src/styles.css`
