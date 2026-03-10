## Notebook Jobs Frontend

Modern React frontend for interacting with the Django notebook platform API. Provides a streamlined UI for notebook management, job submission, and real-time status monitoring.

### What it does

- **API Token Generation**: Generate API tokens directly from the frontend with one click
- **Notebook Selection**: Automatically load and select from your available notebooks via dropdown
- **Job Submission**: Submit notebook jobs with parameters and file uploads
- **Job Monitoring**: Real-time job status tracking with logs and results downloads
- **File Handling**: Drag-and-drop support for input files (.xlsx, .xls, .ipynb, .json, .csv)

This frontend wraps the existing Django REST API in a modern, user-friendly UI with real-time updates and better UX.

### Getting started

From the repo root:

```bash
cd frontend
npm install          # or pnpm/yarn (for the 1st time)
npm run dev
```

Then open the URL printed by Vite (by default `http://localhost:5173`).

### Quick start workflow

1. **Open the app**: Navigate to `http://localhost:5173`
2. **Enter Base URL**: Set to `http://localhost:8000` (or your backend URL)
3. **Click "Generate Token"**: Creates and auto-fills API token (requires login to Dashboard)
4. **Select Notebook**: Choose from dropdown of your notebooks
5. **Add Parameters**: JSON for scalar values, upload files
6. **Submit Job**: Click "Submit Job" to queue execution
7. **Check Status**: Job ID auto-fills; click "Check Status" to monitor

### Accessing Django Admin Interface

The frontend integrates with the Django backend for authentication and notebook management. Here are the key pages you'll need:

#### Login Page
- **URL**: `http://localhost:8000/login/`
- **Purpose**: Authenticate to access the dashboard and generate API tokens
- **Default Credentials**: 
  - Username: `admin`
  - Password: `password123`
- **Navigation**: Click "Log In" link or navigate directly to `/login/`

#### Dashboard Page  
- **URL**: `http://localhost:8000/dashboard/`
- **Purpose**: Upload notebooks, view job history, generate API tokens
- **Features**:
  - Upload new notebooks (.ipynb files)
  - View all your notebooks and jobs
  - Generate API tokens for frontend use
  - Delete notebooks and jobs
- **Navigation**: After login, you'll be redirected to `/dashboard/` automatically

#### Navigation Flow
1. **Start**: Go to `http://localhost:8000/login/` and log in
2. **Dashboard**: Access `http://localhost:8000/dashboard/` to manage notebooks
3. **Token Generation**: Use "Generate API Token" button in dashboard
4. **Frontend**: Switch to `http://localhost:5174` and paste token
5. **Job Management**: Submit and monitor jobs through the frontend

### API Endpoints Used

All endpoints require token authentication via `Authorization: Token <your_token>` header.

#### Token Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/token/status/` | Check if user has active token |
| `POST` | `/api/token/generate/` | Generate new authentication token |

#### Notebooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/notebooks/` | List all notebooks owned by authenticated user |
| `POST` | `/api/notebooks/<notebook_id>/run/` | Submit a job to run a specific notebook |

#### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/jobs/<job_id>/status/` | Get current status of a job |
| `GET` | `/api/jobs/<job_id>/logs/` | Get execution logs for a job |
| `POST` | `/api/jobs/<job_id>/complete/` | Webhook callback (internal - worker reports completion) |
| `GET` | `/api/jobs/poll-status/` | Get status of multiple recent jobs |

### Request/Response Examples

#### 1. Generate Token
```bash
POST /api/token/generate/
Authorization: <session_cookie>
```
**Response (201)**:
```json
{
  "token": "abc123def456xyz"
}
```

#### 2. List Notebooks
```bash
GET /api/notebooks/
Authorization: Token <your_token>
```
**Response (200)**:
```json
{
  "notebooks": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Data Cleaning Demo",
      "created_at": "2026-03-07T10:30:00Z",
      "description": "Cleans and processes raw data"
    }
  ]
}
```

#### 3. Trigger Notebook Run
```bash
POST /api/notebooks/<notebook_id>/run/
Authorization: Token <your_token>
Content-Type: multipart/form-data

param_09_years=5
param_01_input_data_filename=<file.xlsx>
```
**Response (202)**:
```json
{
  "message": "Job successfully queued.",
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "PENDING"
}
```

#### 4. Get Job Status
```bash
GET /api/jobs/<job_id>/status/
Authorization: Token <your_token>
```
**Response (200)**:
```json
{
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "SUCCESS",
  "logs": "Environment built. Starting notebook execution...",
  "download_url": "http://localhost:8000/media/jobs/result_archive.zip"
}
```

### Features

#### ✨ User Interface
- **Real-time Notebook Loading**: Automatically fetches available notebooks after token generation
- **Smart Form Validation**: Disables submit buttons until all required fields are filled
- **Status Badges**: Color-coded job status (green for SUCCESS, red for FAILED, blue for RUNNING)
- **Auto-Fill Job ID**: Job ID from submission automatically appears in status check card
- **Error Handling**: Clear error messages for debugging API issues

#### 📁 File Handling
- **Drag & Drop**: Drop files directly into the drop zone
- **File Type Filtering**: Supports `.xlsx`, `.xls`, `.ipynb`, `.json`, `.csv`
- **Duplicate Prevention**: Prevents uploading files with same name
- **File Preview**: Shows file size and name
- **Multiple Files**: Support for uploading multiple files

#### 📊 Job Monitoring
- **Live Status Updates**: Get real-time job execution status
- **Execution Logs**: View full logs from notebook execution
- **Result Downloads**: Download output files when job completes
- **Error Messages**: Detailed error information if job fails

### Configuration

The frontend is configured via React state and environment:

- **Base URL**: Configurable per session (defaults to `http://localhost:8000`)
- **Token**: Paste existing token or generate new one
- **CORS**: Ensure backend CORS settings allow `http://localhost:5174`

### Testing

Use the `test.http` file in the repository root to test all endpoints with the REST Client extension for VS Code, Thunder Client, or Postman.

See [../test.http](../test.http) for example requests with sample parameters.

### Architecture

```
frontend/
├── src/
│   ├── App.tsx              # Main application component
│   ├── main.tsx             # React entry point
│   ├── components/
│   │   ├── DropZone.tsx     # File upload drag-and-drop
│   │   └── FilePreview.tsx  # File preview display
│   └── styles.css
├── vite.config.ts           # Vite build configuration
├── tsconfig.json            # TypeScript configuration
└── package.json
```

### Development

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **HTTP Client**: Native `fetch` API
- **UI Framework**: Bootstrap 5 (CSS only)
- **File Handling**: react-dropzone

### Notes & Limitations

- **Authentication**: All endpoints require valid API token (DRF Token auth)
- **CORS**: For non-local deployments, ensure backend CORS is properly configured
- **File Size**: No client-side limits; backend may enforce maximum file sizes
- **Polling**: Status checks are manual; consider implementing auto-polling for production
- **Worker Availability**: Job execution requires Kubernetes/Minikube and worker container running

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Token generation failed" | Make sure you're logged into the Dashboard first |
| Notebooks list is empty | Upload a notebook in the Dashboard first |
| Job submission fails with 404 | Verify notebook ID is correct and you own that notebook |
| Status check times out | Backend may be down; check `http://localhost:8000` |
| CORS errors | Backend CORS settings need to allow frontend origin |

