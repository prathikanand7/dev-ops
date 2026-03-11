import React, { useState, useEffect } from 'react';
import { DropZone } from './components/DropZone';

type RunResponse = {
  message: string;
  job_id: string;
  status: string;
  execution_profile?: string;
  resolved_payload?: unknown;
};

type JobStatusResponse = {
  job_id: string;
  status: string;
  logs?: string;
  download_url?: string;
  error_message?: string;
};

type NotebookOption = {
  id: string;
  name: string;
  created_at?: string;
  description?: string;
};

export const App: React.FC = () => {
  const [baseUrl, setBaseUrl] = useState('http://localhost:8010');
  const [token, setToken] = useState('');
  const [isGeneratingToken, setIsGeneratingToken] = useState(false);
  const [tokenError, setTokenError] = useState<string | null>(null);

  const [notebooks, setNotebooks] = useState<NotebookOption[]>([]);
  const [isLoadingNotebooks, setIsLoadingNotebooks] = useState(false);
  const [notebooksError, setNotebooksError] = useState<string | null>(null);

  const [notebookId, setNotebookId] = useState('');
  const [paramsJson, setParamsJson] = useState('{\n  "param_09_years": 5\n}');
  const [fileParamName, setFileParamName] = useState('param_01_input_data_filename');
  const [executionProfile, setExecutionProfile] = useState<'standard' | 'ec2_200gb'>('standard');
  const [dataFiles, setDataFiles] = useState<File[]>([]);

  const [runResult, setRunResult] = useState<RunResponse | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const [jobId, setJobId] = useState('');
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(false);

  // Load notebooks when token changes
  useEffect(() => {
    if (token && baseUrl) {
      fetchNotebooks();
    }
  }, [token, baseUrl]);

  async function handleGenerateToken() {
    setTokenError(null);
    setIsGeneratingToken(true);

    try {
      // Check if user is authenticated by checking /api/token/status/
      const statusRes = await fetch(
        `${baseUrl.replace(/\/$/, '')}/api/token/status/`,
        {
          credentials: 'include',
        },
      );

      if (!statusRes.ok) {
        setTokenError(
          'Please log in to the Dashboard first to generate a token. Navigate to the "Log In" section of the Notebook Ops Platform.',
        );
        return;
      }

      // Generate new token
      const generateRes = await fetch(
        `${baseUrl.replace(/\/$/, '')}/api/token/generate/`,
        {
          method: 'POST',
          credentials: 'include',
        },
      );

      if (!generateRes.ok) {
        const text = await generateRes.text();
        setTokenError(`Failed to generate token: ${text}`);
        return;
      }

      const data = (await generateRes.json()) as { token: string };
      setToken(data.token);
      setTokenError(null);
    } catch (err) {
      setTokenError((err as Error).message);
    } finally {
      setIsGeneratingToken(false);
    }
  }

  async function fetchNotebooks() {
    setNotebooksError(null);
    setIsLoadingNotebooks(true);

    try {
      const url = `${baseUrl.replace(/\/$/, '')}/api/notebooks/`;
      const res = await fetch(url, {
        headers: {
          Authorization: `Token ${token}`,
        },
      });

      if (!res.ok) {
        const text = await res.text();
        setNotebooksError(`Failed to load notebooks: ${text}`);
        return;
      }

      const data = (await res.json()) as
        | NotebookOption[]
        | { notebooks?: NotebookOption[]; results?: NotebookOption[] };

      const notebookItems = Array.isArray(data)
        ? data
        : Array.isArray(data.notebooks)
          ? data.notebooks
          : Array.isArray(data.results)
            ? data.results
            : [];

      setNotebooks(notebookItems);
    } catch (err) {
      setNotebooksError((err as Error).message);
    } finally {
      setIsLoadingNotebooks(false);
    }
  }

  async function handleRunNotebook(e: React.FormEvent) {
    e.preventDefault();
    setRunError(null);
    setRunResult(null);
    setIsRunning(true);

    let parsedParams: Record<string, unknown> = {};
    if (paramsJson.trim()) {
      try {
        parsedParams = JSON.parse(paramsJson);
      } catch (err) {
        setRunError('Parameters JSON is invalid.');
        setIsRunning(false);
        return;
      }
    }

    try {
      const url = `${baseUrl.replace(/\/$/, '')}/api/notebooks/${notebookId}/run/`;

      const formData = new FormData();
      Object.entries(parsedParams).forEach(([key, value]) => {
        formData.append(key, String(value));
      });
      formData.append('execution_profile', executionProfile);

      if (dataFiles.length > 0) {
        const baseName = fileParamName.trim() || 'file';
        dataFiles.forEach((file, index) => {
          const fieldName = index === 0 ? baseName : `${baseName}_${index + 1}`;
          formData.append(fieldName, file);
        });
      }

      const res = await fetch(url, {
        method: 'POST',
        headers: {
          Authorization: `Token ${token}`,
        },
        body: formData,
      });

      if (!res.ok) {
        const text = await res.text();
        setRunError(`Request failed (${res.status}): ${text}`);
        return;
      }

      const data = (await res.json()) as RunResponse;
      setRunResult(data);
      setJobId(data.job_id);
    } catch (err) {
      setRunError((err as Error).message);
    } finally {
      setIsRunning(false);
    }
  }

  async function handleCheckStatus(e: React.FormEvent) {
    e.preventDefault();
    setJobError(null);
    setJobStatus(null);
    setIsChecking(true);

    try {
      const url = `${baseUrl.replace(/\/$/, '')}/api/jobs/${jobId}/status/`;
      const res = await fetch(url, {
        headers: {
          Authorization: `Token ${token}`,
        },
      });

      if (!res.ok) {
        const text = await res.text();
        setJobError(`Request failed (${res.status}): ${text}`);
        return;
      }

      const data = (await res.json()) as JobStatusResponse;
      setJobStatus(data);
    } catch (err) {
      setJobError((err as Error).message);
    } finally {
      setIsChecking(false);
    }
  }

  return (
    <>
      <nav className="navbar navbar-dark bg-dark mb-4">
        <div className="container">
          <span className="navbar-brand text-decoration-none">Notebook Ops Platform</span>
        </div>
      </nav>

      <div className="container mb-5">
        <div className="row mb-4">
          <div className="col-lg-8 mx-auto">
            <div className="card shadow-sm">
              <div className="card-header bg-primary text-white">
                <h4 className="mb-0">API Connection</h4>
              </div>
              <div className="card-body">
                <div className="mb-3">
                  <label htmlFor="base-url" className="form-label">
                    Base URL
                  </label>
                  <input
                    id="base-url"
                    type="text"
                    className="form-control"
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                  />
                </div>
                <div className="mb-3">
                  <label htmlFor="token" className="form-label">
                    API Token
                  </label>
                  <div className="input-group">
                    <input
                      id="token"
                      type="password"
                      className="form-control"
                      value={token}
                      onChange={(e) => setToken(e.target.value)}
                      placeholder="Generate or paste your API token"
                      disabled={isGeneratingToken}
                    />
                    <button
                      className="btn btn-outline-secondary"
                      type="button"
                      onClick={handleGenerateToken}
                      disabled={isGeneratingToken || !baseUrl}
                    >
                      {isGeneratingToken ? 'Generating...' : 'Generate Token'}
                    </button>
                  </div>
                  {tokenError && <div className="form-text text-danger">{tokenError}</div>}
                  {token && <div className="form-text text-success">✓ Token loaded</div>}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="row g-4">
          <div className="col-lg-6">
            <div className="card shadow-sm h-100">
              <div className="card-header bg-white border-bottom">
                <h5 className="mb-0">Trigger Notebook Run</h5>
              </div>
              <div className="card-body">
                <form onSubmit={handleRunNotebook}>
                  <div className="mb-3">
                    <label htmlFor="notebook-select" className="form-label">
                      Select Notebook
                    </label>
                    {isLoadingNotebooks ? (
                      <div className="spinner-border spinner-border-sm" role="status">
                        <span className="visually-hidden">Loading notebooks...</span>
                      </div>
                    ) : (
                      <>
                        <select
                          id="notebook-select"
                          className="form-select"
                          value={notebookId}
                          onChange={(e) => setNotebookId(e.target.value)}
                          required
                          disabled={!token}
                        >
                          <option value="">-- Select a notebook --</option>
                          {notebooks.map((nb) => (
                            <option key={nb.id} value={nb.id}>
                              {nb.name || nb.id}
                            </option>
                          ))}
                        </select>
                        {notebooksError && (
                          <div className="form-text text-danger">{notebooksError}</div>
                        )}
                        {notebooks.length === 0 && token && !isLoadingNotebooks && (
                          <div className="form-text text-muted">
                            No notebooks found. Upload one in the Dashboard.
                          </div>
                        )}
                      </>
                    )}
                  </div>

                  <div className="mb-3">
                    <label htmlFor="params-json" className="form-label">
                      Parameters JSON{' '}
                      <span className="text-muted">(optional scalar params such as numbers/strings)</span>
                    </label>
                    <textarea
                      id="params-json"
                      className="form-control"
                      value={paramsJson}
                      onChange={(e) => setParamsJson(e.target.value)}
                      rows={5}
                    />
                  </div>

                  <div className="mb-3">
                    <label htmlFor="file-param-name" className="form-label">
                      File parameter name
                    </label>
                    <input
                      id="file-param-name"
                      type="text"
                      className="form-control"
                      value={fileParamName}
                      onChange={(e) => setFileParamName(e.target.value)}
                      placeholder="param_01_input_data_filename"
                    />
                    <div className="form-text">
                      Must match the file parameter key expected by your notebook schema.
                    </div>
                  </div>

                  <div className="mb-3">
                    <label htmlFor="execution-profile" className="form-label">
                      Execution profile
                    </label>
                    <select
                      id="execution-profile"
                      className="form-select"
                      value={executionProfile}
                      onChange={(e) =>
                        setExecutionProfile(e.target.value as 'standard' | 'ec2_200gb')
                      }
                    >
                      <option value="standard">Standard</option>
                      <option value="ec2_200gb">Large EC2 (200GB)</option>
                    </select>
                    <div className="form-text">
                      Use <code>ec2_200gb</code> for high storage workloads.
                    </div>
                  </div>

                  <DropZone
                    label="Input files (.xlsx / .ipynb). These will be attached under the parameter name above."
                    onFilesChange={setDataFiles}
                  />

                  <button
                    type="submit"
                    className="btn btn-success mt-2"
                    disabled={isRunning || !token || !notebookId}
                  >
                    {isRunning ? 'Submitting…' : 'Submit Job'}
                  </button>

                  {runError && <div className="alert alert-danger mt-3 mb-0">{runError}</div>}

                  {runResult && (
                    <div className="alert alert-success mt-3 mb-0">
                      <h6 className="mb-1">Job Queued</h6>
                      <p className="mb-1">
                        <strong>Job ID:</strong> {runResult.job_id}
                      </p>
                      <p className="mb-1">
                        <strong>Status:</strong> {runResult.status}
                      </p>
                      <p className="mb-1">
                        <strong>Execution profile:</strong>{' '}
                        {runResult.execution_profile || executionProfile}
                      </p>
                      {runResult.message && (
                        <p className="mb-0">
                          <strong>Message:</strong> {runResult.message}
                        </p>
                      )}
                    </div>
                  )}
                </form>
              </div>
            </div>
          </div>

          <div className="col-lg-6">
            <div className="card shadow-sm h-100">
              <div className="card-header bg-white border-bottom">
                <h5 className="mb-0">Job Status</h5>
              </div>
              <div className="card-body">
                <form onSubmit={handleCheckStatus}>
                  <div className="mb-3">
                    <label htmlFor="job-id" className="form-label">
                      Job ID (UUID)
                    </label>
                    <input
                      id="job-id"
                      type="text"
                      className="form-control"
                      value={jobId}
                      onChange={(e) => setJobId(e.target.value)}
                      placeholder="Paste Job ID from the left card"
                      required
                    />
                    {runResult && (
                      <div className="form-text">
                        💡 Auto-filled from submission: <code>{runResult.job_id.substring(0, 8)}...</code>
                      </div>
                    )}
                  </div>

                  <button
                    type="submit"
                    className="btn btn-outline-primary"
                    disabled={isChecking || !token || !jobId}
                  >
                    {isChecking ? 'Checking…' : 'Check Status'}
                  </button>

                  {jobError && <div className="alert alert-danger mt-3 mb-0">{jobError}</div>}

                  {jobStatus && (
                    <div className="mt-3">
                      <h6>Current Status</h6>
                      <p className="mb-1">
                        <strong>Status:</strong>{' '}
                        <span
                          className={`badge ${
                            jobStatus.status === 'SUCCESS'
                              ? 'bg-success'
                              : jobStatus.status === 'FAILED'
                                ? 'bg-danger'
                                : 'bg-info'
                          }`}
                        >
                          {jobStatus.status}
                        </span>
                      </p>
                      {jobStatus.download_url && (
                        <p className="mb-1">
                          <strong>Download:</strong>{' '}
                          <a href={jobStatus.download_url} target="_blank" rel="noreferrer">
                            Open results
                          </a>
                        </p>
                      )}
                      {jobStatus.error_message && (
                        <p className="mb-1 text-danger">
                          <strong>Error:</strong> {jobStatus.error_message}
                        </p>
                      )}
                      {jobStatus.logs && (
                        <div className="mt-2">
                          <p className="mb-1">
                            <strong>Logs:</strong>
                          </p>
                          <pre className="logs p-2 bg-dark text-light rounded">{jobStatus.logs}</pre>
                        </div>
                      )}
                    </div>
                  )}
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
