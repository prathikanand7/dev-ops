import React, { useEffect, useMemo, useRef, useState } from 'react';
import { DropZone } from './components/DropZone';

type RunResponse = {
  message: string;
  job_id: string;
  batch_job_id?: string;
  execution_profile?: string;
};

type JobStatusResponse = {
  job_id: string;
  job_name?: string;
  status: string;
  createdAt?: number;
  startedAt?: number;
  stoppedAt?: number;
  error?: string;
};

type JobLogsResponse = {
  job_id: string;
  logs: string[];
};

type JobResultsResponse = {
  job_id: string;
  status?: string;
  download_url?: string;
  results: Array<{
    filename: string;
    content_base64: string;
  }>;
};

export const App: React.FC = () => {
  const [baseUrl, setBaseUrl] = useState(
    'https://hm2jyuxlpd.execute-api.eu-west-1.amazonaws.com/dev',
  );
  const [apiKey, setApiKey] = useState('');
  const [paramsJson, setParamsJson] = useState('{\n  "param_09_years": 5\n}');
  const [fileParamName, setFileParamName] = useState('param_01_input_data_filename');
  const [executionProfile, setExecutionProfile] = useState<'standard' | 'ec2_200gb'>('standard');
  const [files, setFiles] = useState<File[]>([]);
  const [extractInfo, setExtractInfo] = useState<string | null>(null);

  const [runResult, setRunResult] = useState<RunResponse | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [jobId, setJobId] = useState('');
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [statusUpdatedAt, setStatusUpdatedAt] = useState<Date | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const [jobInfo, setJobInfo] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [isFetchingLogs, setIsFetchingLogs] = useState(false);
  const [isFetchingResults, setIsFetchingResults] = useState(false);
  const [jobLogs, setJobLogs] = useState<string[]>([]);
  const [jobResults, setJobResults] = useState<JobResultsResponse['results']>([]);
  const [resultsDownloadUrl, setResultsDownloadUrl] = useState<string | null>(null);
  const [resultsError, setResultsError] = useState<string | null>(null);
  const [resultsInfo, setResultsInfo] = useState<string | null>(null);

  const pollRef = useRef<number | null>(null);
  const autoFetchResultsForJobRef = useRef<string | null>(null);

  const normalizedBaseUrl = useMemo(() => baseUrl.replace(/\/$/, ''), [baseUrl]);
  const currentJobStatus = jobStatus?.status || '';
  const logsReadyStatuses = ['RUNNING', 'SUCCEEDED', 'FAILED'];
  const canFetchLogsNow = logsReadyStatuses.includes(currentJobStatus);
  const canFetchResultsNow = currentJobStatus === 'SUCCEEDED';

  useEffect(() => {
    return () => {
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!jobId || !apiKey) {
      return;
    }

    if (jobStatus?.status !== 'SUCCEEDED') {
      return;
    }

    if (resultsDownloadUrl || isFetchingResults) {
      return;
    }

    if (autoFetchResultsForJobRef.current === jobId) {
      return;
    }

    autoFetchResultsForJobRef.current = jobId;
    void handleFetchResults();
  }, [jobId, apiKey, jobStatus?.status, resultsDownloadUrl, isFetchingResults]);

  function decodeApiBody<T>(raw: unknown): T {
    if (typeof raw === 'string') {
      try {
        return JSON.parse(raw) as T;
      } catch {
        throw new Error(`API returned a non-JSON string body: ${raw}`);
      }
    }

    return raw as T;
  }

  function readFileAsText(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = () => {
        if (typeof reader.result !== 'string') {
          reject(new Error('FileReader result is not text.'));
          return;
        }

        resolve(reader.result);
      };

      reader.onerror = () => {
        reject(reader.error || new Error('Failed to read file with FileReader.'));
      };

      reader.readAsText(file);
    });
  }

  function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => {
      window.setTimeout(resolve, ms);
    });
  }

  function parseNotebookParameters(notebookText: string): Record<string, string | number | boolean> {
    const notebook = JSON.parse(notebookText) as {
      cells?: Array<{
        cell_type?: string;
        metadata?: { tags?: string[] };
        source?: string[];
      }>;
    };

    const parameterCell = notebook.cells?.find(
      (cell) => cell.cell_type === 'code' && Array.isArray(cell.metadata?.tags) && cell.metadata.tags.includes('parameters'),
    );

    if (!parameterCell?.source?.length) {
      return {};
    }

    const extracted: Record<string, string | number | boolean> = {};
    const assignmentRegex = /^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:<-|=)\s*(.+?)\s*$/;

    parameterCell.source.forEach((rawLine) => {
      const line = rawLine.trim();

      if (!line || line.startsWith('#')) {
        return;
      }

      const match = line.match(assignmentRegex);
      if (!match) {
        return;
      }

      const [, key, valueRaw] = match;
      let value: string | number | boolean = valueRaw;

      if (/^[-+]?\d+(?:\.\d+)?$/.test(valueRaw)) {
        value = Number(valueRaw);
      } else if (/^(true|false)$/i.test(valueRaw)) {
        value = valueRaw.toLowerCase() === 'true';
      } else {
        value = valueRaw.replace(/^['"]|['"]$/g, '');
      }

      extracted[key] = value;
    });

    return extracted;
  }

  async function extractParametersFromNotebook(notebookFile: File): Promise<void> {
    try {
      const text = await readFileAsText(notebookFile);
      const extracted = parseNotebookParameters(text);

      if (Object.keys(extracted).length === 0) {
        setExtractInfo('Notebook loaded, but no tagged parameters cell was found.');
        return;
      }

      setParamsJson(JSON.stringify(extracted, null, 2));
      setExtractInfo('Parameters extracted from notebook and prefilled.');
    } catch (error) {
      setExtractInfo(`Failed to parse notebook: ${(error as Error).message}`);
    }
  }

  async function handleFilesChange(newFiles: File[]): Promise<void> {
    setFiles(newFiles);

    const notebookFile = newFiles.find((file) => file.name.toLowerCase().endsWith('.ipynb'));
    if (notebookFile) {
      await extractParametersFromNotebook(notebookFile);
    } else {
      setExtractInfo(null);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setRunError(null);
    setRunResult(null);
    setJobError(null);
    setJobInfo(null);
    setJobStatus(null);
    setJobLogs([]);
    setJobResults([]);
    setResultsDownloadUrl(null);
    setResultsError(null);
    setResultsInfo(null);
    autoFetchResultsForJobRef.current = null;
    setIsSubmitting(true);

    let parsedParams: Record<string, unknown> = {};
    if (paramsJson.trim()) {
      try {
        parsedParams = JSON.parse(paramsJson);
      } catch (err) {
        setRunError('Parameters JSON is invalid.');
        setIsSubmitting(false);
        return;
      }
    }

    try {
      const url = `${normalizedBaseUrl}/batch/jobs`;

      const formData = new FormData();

      const notebookFile = files.find((file) => file.name.toLowerCase().endsWith('.ipynb'));
      if (!notebookFile) {
        setRunError('You must include one .ipynb notebook file.');
        setIsSubmitting(false);
        return;
      }

      formData.append('notebook', notebookFile, notebookFile.name);

      Object.entries(parsedParams).forEach(([key, value]) => {
        if (key.trim()) {
          formData.append(key, String(value));
        }
      });

      formData.append('execution_profile', executionProfile);

      const nonNotebookFiles = files.filter((file) => !file.name.toLowerCase().endsWith('.ipynb'));
      if (nonNotebookFiles.length > 0) {
        const baseName = fileParamName.trim() || 'param_01_input_data_filename';

        nonNotebookFiles.forEach((file, index) => {
          const fieldName = index === 0 ? baseName : `upload_${String(index).padStart(2, '0')}`;
          formData.append(fieldName, file);
        });

        if (!(baseName in parsedParams)) {
          formData.append(baseName, nonNotebookFiles[0].name);
        }
      }

      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'x-api-key': apiKey,
        },
        body: formData,
      });

      if (!res.ok) {
        const text = await res.text();
        setRunError(`Request failed (${res.status}): ${text}`);
        return;
      }

      const rawData = (await res.json()) as unknown;
      const data = decodeApiBody<RunResponse>(rawData);
      setRunResult(data);
      setJobId(data.job_id);
      startPolling(data.job_id);
    } catch (err) {
      setRunError((err as Error).message);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function fetchStatus(
    targetJobId: string,
    options?: { suppressError?: boolean },
  ): Promise<JobStatusResponse | null> {
    const suppressError = options?.suppressError ?? false;

    if (!suppressError) {
      setJobError(null);
    }

    try {
      const url = `${normalizedBaseUrl}/batch/jobs/${targetJobId}`;
      const res = await fetch(url, {
        headers: {
          'x-api-key': apiKey,
        },
      });

      if (!res.ok) {
        const text = await res.text();
        if (!suppressError) {
          setJobError(`Request failed (${res.status}): ${text}`);
        }
        return null;
      }

      const rawData = (await res.json()) as unknown;
      const data = decodeApiBody<JobStatusResponse>(rawData);
      setJobStatus(data);
      setStatusUpdatedAt(new Date());
      return data;
    } catch (err) {
      if (!suppressError) {
        setJobError((err as Error).message);
      }
      return null;
    }
  }

  async function handleCheckStatus(e: React.FormEvent) {
    e.preventDefault();
    setIsChecking(true);
    setJobInfo(null);

    try {
      await fetchStatus(jobId);
    } finally {
      setIsChecking(false);
    }
  }

  function startPolling(targetJobId: string): void {
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
    }

    pollRef.current = window.setInterval(async () => {
      const status = await fetchStatus(targetJobId);

      if (!status) {
        return;
      }

      const terminalStatuses = ['SUCCEEDED', 'FAILED'];
      if (terminalStatuses.includes(status.status)) {
        if (pollRef.current) {
          window.clearInterval(pollRef.current);
          pollRef.current = null;
        }
      }
    }, 10000);
  }

  async function handleFetchLogs() {
    if (!jobId.trim()) {
      return;
    }

    setIsFetchingLogs(true);
    setJobError(null);
    setJobInfo(null);

    try {
      const status = (await fetchStatus(jobId, { suppressError: true })) || jobStatus;
      const statusValue = status?.status || '';

      if (!logsReadyStatuses.includes(statusValue)) {
        setJobLogs([]);
        setJobInfo('Job is still being submitted/started. Logs are available once status is RUNNING.');
        return;
      }

      const res = await fetch(`${normalizedBaseUrl}/batch/jobs/${jobId}/logs`, {
        headers: {
          'x-api-key': apiKey,
        },
      });

      if (!res.ok) {
        const text = await res.text();

        if (res.status === 500 && /log stream does not exist/i.test(text)) {
          setJobInfo('Job is running but log stream is not ready yet. Please try again in a few moments.');
          return;
        }

        setJobError(`Logs request failed (${res.status}): ${text}`);
        return;
      }

      const rawData = (await res.json()) as unknown;
      const data = decodeApiBody<JobLogsResponse>(rawData);
      setJobLogs(data.logs || []);
    } catch (error) {
      setJobError((error as Error).message);
    } finally {
      setIsFetchingLogs(false);
    }
  }

  async function handleFetchResults() {
    if (!jobId.trim()) {
      return;
    }

    setIsFetchingResults(true);
    setResultsError(null);
    setResultsInfo(null);
    setResultsDownloadUrl(null);

    try {
      const status = (await fetchStatus(jobId, { suppressError: true })) || jobStatus;
      if (status?.status !== 'SUCCEEDED') {
        setJobResults([]);
        setResultsDownloadUrl(null);
        setResultsInfo('Job has not succeeded yet. Results URL becomes available only after SUCCEEDED status.');
        return;
      }

      const maxAttempts = 8;
      const retryDelayMs = 2500;

      for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
        const res = await fetch(`${normalizedBaseUrl}/batch/jobs/${jobId}/results`, {
          headers: {
            'x-api-key': apiKey,
          },
        });

        if (!res.ok) {
          const text = await res.text();

          if (res.status === 404 && attempt < maxAttempts) {
            setResultsInfo(`Job succeeded. Preparing downloadable ZIP... (${attempt}/${maxAttempts})`);
            await sleep(retryDelayMs);
            continue;
          }

          if (res.status === 404) {
            setJobResults([]);
            setResultsDownloadUrl(null);
            setResultsInfo('Job succeeded, but results are still being packaged. Please try again in a few moments.');
            return;
          }

          setResultsError(`Results request failed (${res.status}): ${text}`);
          return;
        }

        const rawData = (await res.json()) as unknown;
        const data = decodeApiBody<JobResultsResponse>(rawData);

        if (data.download_url) {
          setJobResults([]);
          setResultsDownloadUrl(data.download_url);
          setResultsInfo('Results ZIP is ready to download.');
          return;
        }

        if (Array.isArray(data.results) && data.results.length > 0) {
          setResultsDownloadUrl(null);
          setJobResults(data.results);
          return;
        }

        if (attempt < maxAttempts) {
          setResultsInfo(`Job succeeded. Waiting for results URL... (${attempt}/${maxAttempts})`);
          await sleep(retryDelayMs);
          continue;
        }

        setJobResults([]);
        setResultsDownloadUrl(null);
        setResultsInfo('Job succeeded, but results URL is not ready yet. Please try again shortly.');
      }
    } catch (error) {
      setResultsError((error as Error).message);
    } finally {
      setIsFetchingResults(false);
    }
  }

  function downloadResultFile(filename: string, contentBase64: string): void {
    const bytes = window.atob(contentBase64);
    const array = new Uint8Array(bytes.length);

    for (let i = 0; i < bytes.length; i += 1) {
      array[i] = bytes.charCodeAt(i);
    }

    const blob = new Blob([array]);
    const blobUrl = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = blobUrl;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(blobUrl);
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
                  <label htmlFor="api-key" className="form-label">
                    API Key
                  </label>
                  <input
                    id="api-key"
                    type="password"
                    className="form-control"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Paste your API Gateway key"
                  />
                  <div className="form-text">Used as <code>x-api-key</code> for Lambda API Gateway routes.</div>
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
                <form onSubmit={handleSubmit}>
                  <div className="mb-3">
                    <label htmlFor="params-json" className="form-label">
                      Parameters JSON
                      <span className="text-muted"> (sent as multipart fields)</span>
                    </label>
                    <textarea
                      id="params-json"
                      className="form-control"
                      value={paramsJson}
                      onChange={(e) => setParamsJson(e.target.value)}
                      rows={5}
                    />
                    {extractInfo && <div className="form-text text-info">{extractInfo}</div>}
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
                      First uploaded data file is also mapped to this parameter value if missing in JSON.
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
                    label="Drop one .ipynb notebook and optional data files (.xlsx/.xls)."
                    onFilesChange={handleFilesChange}
                  />

                  <button
                    type="submit"
                    className="btn btn-success mt-2"
                    disabled={isSubmitting || !apiKey || files.length === 0}
                  >
                    {isSubmitting ? 'Submitting…' : 'Submit Job'}
                  </button>

                  {runError && <div className="alert alert-danger mt-3 mb-0">{runError}</div>}

                  {runResult && (
                    <div className="alert alert-success mt-3 mb-0">
                      <h6 className="mb-1">Job Queued</h6>
                      <p className="mb-1">
                        <strong>Job ID:</strong> {runResult.job_id}
                      </p>
                      <p className="mb-1">
                        <strong>Batch Job ID:</strong> {runResult.batch_job_id || 'n/a'}
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
                        Auto-filled from submission: <code>{runResult.job_id.substring(0, 8)}...</code>
                      </div>
                    )}
                  </div>

                  <button
                    type="submit"
                    className="btn btn-outline-primary"
                    disabled={isChecking || !apiKey || !jobId}
                  >
                    {isChecking ? 'Checking…' : 'Check Status'}
                  </button>

                  <button
                    type="button"
                    className="btn btn-outline-secondary ms-2"
                    onClick={handleFetchLogs}
                    disabled={isFetchingLogs || !apiKey || !jobId}
                  >
                    {isFetchingLogs
                      ? 'Loading Logs…'
                      : !canFetchLogsNow && !!jobId
                        ? 'Wait For RUNNING'
                        : 'Fetch Logs'}
                  </button>

                  <button
                    type="button"
                    className="btn btn-outline-success ms-2"
                    onClick={handleFetchResults}
                    disabled={isFetchingResults || !apiKey || !jobId}
                  >
                    {isFetchingResults
                      ? 'Waiting For ZIP…'
                      : !canFetchResultsNow && !!jobId
                        ? 'Wait For SUCCEEDED'
                        : 'Fetch Results'}
                  </button>

                  {jobError && <div className="alert alert-danger mt-3 mb-0">{jobError}</div>}
                  {jobInfo && <div className="alert alert-info mt-3 mb-0">{jobInfo}</div>}

                  {jobStatus && (
                    <div className="mt-3">
                      <h6>Current Status</h6>
                      {statusUpdatedAt && (
                        <p className="mb-1 text-muted small">
                          Last updated: {statusUpdatedAt.toLocaleString()}
                        </p>
                      )}
                      <p className="mb-1">
                        <strong>Status:</strong>{' '}
                        <span
                          className={`badge ${
                            jobStatus.status === 'SUCCEEDED'
                              ? 'bg-success'
                              : jobStatus.status === 'FAILED'
                                ? 'bg-danger'
                                : 'bg-info'
                          }`}
                        >
                          {jobStatus.status}
                        </span>
                      </p>
                      {jobStatus.error && (
                        <p className="mb-1 text-danger">
                          <strong>Error:</strong> {jobStatus.error}
                        </p>
                      )}

                      {jobLogs.length > 0 && (
                        <div className="mt-2">
                          <p className="mb-1">
                            <strong>Logs:</strong>
                          </p>
                          <pre className="logs p-2 bg-dark text-light rounded">
                            {jobLogs.join('\n')}
                          </pre>
                        </div>
                      )}

                      {resultsError && <div className="alert alert-warning mt-2 mb-0">{resultsError}</div>}
                      {resultsInfo && <div className="alert alert-info mt-2 mb-0">{resultsInfo}</div>}

                      {resultsDownloadUrl && (
                        <div className="mt-2">
                          <a
                            className="btn btn-sm btn-success"
                            href={resultsDownloadUrl}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Download Results ZIP
                          </a>
                        </div>
                      )}

                      {jobResults.length > 0 && (
                        <div className="mt-3">
                          <p className="mb-2">
                            <strong>Results:</strong>
                          </p>
                          <div className="d-flex flex-column gap-2">
                            {jobResults.map((result) => (
                              <button
                                key={result.filename}
                                type="button"
                                className="btn btn-sm btn-outline-success text-start"
                                onClick={() => downloadResultFile(result.filename, result.content_base64)}
                              >
                                Download {result.filename}
                              </button>
                            ))}
                          </div>
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
