import React, { useEffect, useMemo, useRef, useState } from 'react';
import { BsMoon, BsSun } from 'react-icons/bs';
import {
  FiZap,
  FiRadio,
  FiLink,
  FiPlay,
  FiSearch,
  FiFileText,
  FiPackage,
  FiDownload,
  FiAlertCircle,
  FiInfo,
  FiCheckCircle,
} from 'react-icons/fi';
import { DropZone } from './components/DropZone';

type RunResponse = {
  message: string;
  job_id: string;
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

type ThemeMode = 'dark' | 'light';

export const App: React.FC = () => {
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const saved = window.localStorage.getItem('nop-theme');
    if (saved === 'dark' || saved === 'light') return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  const [baseUrl, setBaseUrl] = useState(
    'https://n69rb6bzvl.execute-api.eu-west-1.amazonaws.com/dev',
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
    return () => { if (pollRef.current) window.clearInterval(pollRef.current); };
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    window.localStorage.setItem('nop-theme', theme);
  }, [theme]);

  useEffect(() => {
    if (!jobId || !apiKey) return;
    if (jobStatus?.status !== 'SUCCEEDED') return;
    if (resultsDownloadUrl || isFetchingResults) return;
    if (autoFetchResultsForJobRef.current === jobId) return;
    autoFetchResultsForJobRef.current = jobId;
    void handleFetchResults();
  }, [jobId, apiKey, jobStatus?.status, resultsDownloadUrl, isFetchingResults]);

  function decodeApiBody<T>(raw: unknown): T {
    if (typeof raw === 'string') {
      try { return JSON.parse(raw) as T; }
      catch { throw new Error(`API returned a non-JSON string body: ${raw}`); }
    }
    return raw as T;
  }

  function readFileAsText(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result !== 'string') { reject(new Error('FileReader result is not text.')); return; }
        resolve(reader.result);
      };
      reader.onerror = () => reject(reader.error || new Error('Failed to read file with FileReader.'));
      reader.readAsText(file);
    });
  }

  function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => { window.setTimeout(resolve, ms); });
  }

  function parseNotebookParameters(notebookText: string): Record<string, string | number | boolean> {
    const notebook = JSON.parse(notebookText) as {
      cells?: Array<{ cell_type?: string; metadata?: { tags?: string[] }; source?: string[] }>;
    };
    const parameterCell = notebook.cells?.find(
      (cell) => cell.cell_type === 'code' && Array.isArray(cell.metadata?.tags) && cell.metadata.tags.includes('parameters'),
    );
    if (!parameterCell?.source?.length) return {};
    const extracted: Record<string, string | number | boolean> = {};
    const assignmentRegex = /^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:<-|=)\s*(.+?)\s*$/;
    parameterCell.source.forEach((rawLine) => {
      const line = rawLine.trim();
      if (!line || line.startsWith('#')) return;
      const match = line.match(assignmentRegex);
      if (!match) return;
      const [, key, valueRaw] = match;
      let value: string | number | boolean = valueRaw;
      if (/^[-+]?\d+(?:\.\d+)?$/.test(valueRaw)) value = Number(valueRaw);
      else if (/^(true|false)$/i.test(valueRaw)) value = valueRaw.toLowerCase() === 'true';
      else value = valueRaw.replace(/^['"]|['"]$/g, '');
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
    const notebookFile = newFiles.find((f) => f.name.toLowerCase().endsWith('.ipynb'));
    if (notebookFile) await extractParametersFromNotebook(notebookFile);
    else setExtractInfo(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setRunError(null); setRunResult(null); setJobError(null); setJobInfo(null);
    setJobStatus(null); setJobLogs([]); setJobResults([]);
    setResultsDownloadUrl(null); setResultsError(null); setResultsInfo(null);
    autoFetchResultsForJobRef.current = null;
    setIsSubmitting(true);

    let parsedParams: Record<string, unknown> = {};
    if (paramsJson.trim()) {
      try { parsedParams = JSON.parse(paramsJson); }
      catch { setRunError('Parameters JSON is invalid.'); setIsSubmitting(false); return; }
    }

    try {
      const url = `${normalizedBaseUrl}/batch/jobs`;
      const formData = new FormData();
      const notebookFile = files.find((f) => f.name.toLowerCase().endsWith('.ipynb'));
      if (!notebookFile) { setRunError('You must include one .ipynb notebook file.'); setIsSubmitting(false); return; }
      formData.append('notebook', notebookFile, notebookFile.name);
      Object.entries(parsedParams).forEach(([key, value]) => { if (key.trim()) formData.append(key, String(value)); });
      formData.append('execution_profile', executionProfile);
      const nonNotebookFiles = files.filter((f) => !f.name.toLowerCase().endsWith('.ipynb'));
      if (nonNotebookFiles.length > 0) {
        const baseName = fileParamName.trim() || 'param_01_input_data_filename';
        nonNotebookFiles.forEach((f, i) => {
          formData.append(i === 0 ? baseName : `upload_${String(i).padStart(2, '0')}`, f);
        });
        if (!(baseName in parsedParams)) formData.append(baseName, nonNotebookFiles[0].name);
      }
      const res = await fetch(url, { method: 'POST', headers: { 'x-api-key': apiKey }, body: formData });
      if (!res.ok) { const text = await res.text(); setRunError(`Request failed (${res.status}): ${text}`); return; }
      const data = decodeApiBody<RunResponse>((await res.json()) as unknown);
      setRunResult(data);
      setJobId(data.job_id);
      startPolling(data.job_id);
    } catch (err) {
      setRunError((err as Error).message);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function fetchStatus(targetJobId: string, options?: { suppressError?: boolean }): Promise<JobStatusResponse | null> {
    const suppress = options?.suppressError ?? false;
    if (!suppress) setJobError(null);
    try {
      const res = await fetch(`${normalizedBaseUrl}/batch/jobs/${targetJobId}`, { headers: { 'x-api-key': apiKey } });
      if (!res.ok) {
        const text = await res.text();
        if (!suppress) setJobError(`Request failed (${res.status}): ${text}`);
        return null;
      }
      const data = decodeApiBody<JobStatusResponse>((await res.json()) as unknown);
      setJobStatus(data); setStatusUpdatedAt(new Date()); return data;
    } catch (err) {
      if (!suppress) setJobError((err as Error).message);
      return null;
    }
  }

  async function handleCheckStatus(e: React.FormEvent) {
    e.preventDefault(); setIsChecking(true); setJobInfo(null);
    try { await fetchStatus(jobId); } finally { setIsChecking(false); }
  }

  function startPolling(targetJobId: string): void {
    if (pollRef.current) window.clearInterval(pollRef.current);
    pollRef.current = window.setInterval(async () => {
      const status = await fetchStatus(targetJobId);
      if (status && ['SUCCEEDED', 'FAILED'].includes(status.status)) {
        if (pollRef.current) { window.clearInterval(pollRef.current); pollRef.current = null; }
      }
    }, 10000);
  }

  async function handleFetchLogs() {
    if (!jobId.trim()) return;
    setIsFetchingLogs(true); setJobError(null); setJobInfo(null);
    try {
      const status = (await fetchStatus(jobId, { suppressError: true })) || jobStatus;
      if (!logsReadyStatuses.includes(status?.status || '')) {
        setJobLogs([]); setJobInfo('Job is still being submitted/started. Logs are available once status is RUNNING.'); return;
      }
      const res = await fetch(`${normalizedBaseUrl}/batch/jobs/${jobId}/logs`, { headers: { 'x-api-key': apiKey } });
      if (!res.ok) {
        const text = await res.text();
        if (res.status === 500 && /log stream does not exist/i.test(text)) {
          setJobInfo('Job is running but log stream is not ready yet. Please try again in a few moments.'); return;
        }
        setJobError(`Logs request failed (${res.status}): ${text}`); return;
      }
      const data = decodeApiBody<JobLogsResponse>((await res.json()) as unknown);
      setJobLogs(data.logs || []);
    } catch (error) { setJobError((error as Error).message); }
    finally { setIsFetchingLogs(false); }
  }

  async function handleFetchResults() {
    if (!jobId.trim()) return;
    setIsFetchingResults(true); setResultsError(null); setResultsInfo(null); setResultsDownloadUrl(null);
    try {
      const status = (await fetchStatus(jobId, { suppressError: true })) || jobStatus;
      if (status?.status !== 'SUCCEEDED') {
        setJobResults([]); setResultsDownloadUrl(null);
        setResultsInfo('Job has not succeeded yet. Results URL becomes available only after SUCCEEDED status.'); return;
      }
      const maxAttempts = 8; const retryDelayMs = 2500;
      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        const res = await fetch(`${normalizedBaseUrl}/batch/jobs/${jobId}/results`, { headers: { 'x-api-key': apiKey } });
        if (!res.ok) {
          const text = await res.text();
          if (res.status === 404 && attempt < maxAttempts) { setResultsInfo(`Preparing ZIP... (${attempt}/${maxAttempts})`); await sleep(retryDelayMs); continue; }
          if (res.status === 404) { setResultsInfo('Results still being packaged. Try again shortly.'); return; }
          setResultsError(`Results request failed (${res.status}): ${text}`); return;
        }
        const data = decodeApiBody<JobResultsResponse>((await res.json()) as unknown);
        if (data.download_url) { setJobResults([]); setResultsDownloadUrl(data.download_url); setResultsInfo('Results ZIP ready.'); return; }
        if (Array.isArray(data.results) && data.results.length > 0) { setResultsDownloadUrl(null); setJobResults(data.results); return; }
        if (attempt < maxAttempts) { setResultsInfo(`Waiting for results... (${attempt}/${maxAttempts})`); await sleep(retryDelayMs); continue; }
        setResultsInfo('Results URL not ready yet. Please try again shortly.');
      }
    } catch (error) { setResultsError((error as Error).message); }
    finally { setIsFetchingResults(false); }
  }

  function downloadResultFile(filename: string, contentBase64: string): void {
    const bytes = window.atob(contentBase64);
    const array = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) array[i] = bytes.charCodeAt(i);
    const blobUrl = URL.createObjectURL(new Blob([array]));
    const a = document.createElement('a');
    a.href = blobUrl; a.download = filename;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(blobUrl);
  }

  function toggleTheme(): void { setTheme((p) => (p === 'dark' ? 'light' : 'dark')); }

  function getStatusClass(status: string): string {
    if (status === 'SUCCEEDED') return 'status-succeeded';
    if (status === 'FAILED') return 'status-failed';
    if (status === 'RUNNING') return 'status-running';
    return 'status-other';
  }

  return (
    <div className="app-root">

      {/* ── Background ── */}
      <div className="app-bg" aria-hidden="true">
        <div className="app-bg-grid" />
        <div className="app-bg-lines" />
        {/* Static corner glows — GoQuant gradient feel */}
        <div className="app-bg-corner-tl" />
        <div className="app-bg-corner-br" />
        {/* Bouncing light orb — bloom layer + bright core */}
        <div className="app-bg-bulb" />
        <div className="app-bg-bulb-core" />
      </div>

      {/* ── Navbar ── */}
      <nav className="app-navbar">
        <div className="navbar-inner">
          <div className="navbar-brand-area">
            <div className="navbar-logo-dot" aria-hidden="true" />
            <span className="navbar-brand">
              Notebook<span>Ops</span>
            </span>
          </div>
          <button
            type="button"
            className="theme-toggle-btn"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? <BsSun size={13} /> : <BsMoon size={13} />}
            {theme === 'dark' ? 'Light' : 'Dark'}
          </button>
        </div>
      </nav>

      {/* ── Page ── */}
      <div className="page-container">

        {/* API Connection */}
        <div className="row-grid row-grid-center mb-section">
          <div className="glass-card">
            <div className="card-inner">
              <div className="card-head">
                <div className="card-head-icon"><FiLink size={14} /></div>
                <h4>API Connection</h4>
              </div>
              <div className="card-body-inner">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                    <label className="form-label-styled" htmlFor="base-url">Base URL</label>
                    <input id="base-url" type="text" className="form-control-styled" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
                  </div>
                  <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                    <label className="form-label-styled" htmlFor="api-key">API Key</label>
                    <input id="api-key" type="password" className="form-control-styled" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="Paste your API Gateway key" />
                    <p className="form-hint">Sent as <code>x-api-key</code> header on all Lambda API Gateway routes.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Two columns */}
        <div className="row-grid row-grid-2">

          {/* Submit Job */}
          <div className="glass-card">
            <div className="card-inner">
              <div className="card-head">
                <div className="card-head-icon"><FiZap size={14} /></div>
                <h5>Trigger Notebook Run</h5>
              </div>
              <div className="card-body-inner">
                <form onSubmit={handleSubmit}>

                  <div className="form-group">
                    <label className="form-label-styled" htmlFor="params-json">
                      Parameters JSON
                      <span style={{ fontWeight: 400, textTransform: 'none', letterSpacing: 0, color: 'var(--ink-muted)', fontSize: '0.72rem', marginLeft: '0.4rem' }}>
                        (sent as multipart fields)
                      </span>
                    </label>
                    <textarea id="params-json" className="form-control-styled" value={paramsJson} onChange={(e) => setParamsJson(e.target.value)} rows={5} />
                    {extractInfo && (
                      <p className="extract-info">
                        <FiInfo size={11} />
                        {extractInfo}
                      </p>
                    )}
                  </div>

                  <div className="form-group">
                    <label className="form-label-styled" htmlFor="file-param-name">File parameter name</label>
                    <input id="file-param-name" type="text" className="form-control-styled" value={fileParamName} onChange={(e) => setFileParamName(e.target.value)} placeholder="param_01_input_data_filename" />
                    <p className="form-hint">First uploaded data file is also mapped to this parameter value if missing in JSON.</p>
                  </div>

                  <div className="form-group">
                    <label className="form-label-styled" htmlFor="execution-profile">Execution Profile</label>
                    <select id="execution-profile" className="form-control-styled" value={executionProfile} onChange={(e) => setExecutionProfile(e.target.value as 'standard' | 'ec2_200gb')}>
                      <option value="standard">Standard</option>
                      <option value="ec2_200gb">Large EC2 (200GB)</option>
                    </select>
                    <p className="form-hint">Use <code>ec2_200gb</code> for high storage workloads.</p>
                  </div>

                  <DropZone label="Drop one .ipynb notebook and optional data files (.xlsx / .xls)" onFilesChange={handleFilesChange} />

                  <div className="btn-row">
                    <button type="submit" className="btn-neon btn-primary-neon" disabled={isSubmitting || !apiKey || files.length === 0}>
                      <FiPlay size={13} />
                      {isSubmitting ? 'Submitting…' : 'Submit Job'}
                    </button>
                  </div>

                  {runError && (
                    <div className="alert-neon alert-danger-neon">
                      <h6><FiAlertCircle size={11} style={{ marginRight: 4, verticalAlign: 'middle' }} />Error</h6>
                      {runError}
                    </div>
                  )}

                  {runResult && (
                    <div className="alert-neon alert-success-neon">
                      <h6><FiCheckCircle size={11} style={{ marginRight: 4, verticalAlign: 'middle' }} />Job Queued</h6>
                      <div className="kv-row"><span className="kv-label">Job ID</span><span className="kv-value">{runResult.job_id}</span></div>
                      <div className="kv-row"><span className="kv-label">Profile</span><span className="kv-value">{runResult.execution_profile || executionProfile}</span></div>
                      {runResult.message && <div className="kv-row"><span className="kv-label">Message</span><span className="kv-value">{runResult.message}</span></div>}
                    </div>
                  )}
                </form>
              </div>
            </div>
          </div>

          {/* Job Status */}
          <div className="glass-card">
            <div className="card-inner">
              <div className="card-head">
                <div className="card-head-icon"><FiRadio size={14} /></div>
                <h5>Job Status</h5>
              </div>
              <div className="card-body-inner">
                <form onSubmit={handleCheckStatus}>

                  <div className="form-group">
                    <label className="form-label-styled" htmlFor="job-id">Job ID (UUID)</label>
                    <input id="job-id" type="text" className="form-control-styled" value={jobId} onChange={(e) => setJobId(e.target.value)} placeholder="Paste Job ID from the left panel" required />
                    {runResult && <p className="form-hint">Auto-filled from submission: <code>{runResult.job_id.substring(0, 8)}…</code></p>}
                  </div>

                  <div className="btn-row">
                    <button type="submit" className="btn-neon btn-secondary-neon" disabled={isChecking || !apiKey || !jobId}>
                      <FiSearch size={13} />
                      {isChecking ? 'Checking…' : 'Check Status'}
                    </button>

                    <button type="button" className="btn-neon btn-ghost-neon" onClick={handleFetchLogs} disabled={isFetchingLogs || !apiKey || !jobId}>
                      <FiFileText size={13} />
                      {isFetchingLogs ? 'Loading…' : !canFetchLogsNow && !!jobId ? 'Wait for RUNNING' : 'Fetch Logs'}
                    </button>

                    <button type="button" className="btn-neon btn-ghost-neon" onClick={handleFetchResults} disabled={isFetchingResults || !apiKey || !jobId}>
                      <FiPackage size={13} />
                      {isFetchingResults ? 'Waiting for ZIP…' : !canFetchResultsNow && !!jobId ? 'Wait for SUCCEEDED' : 'Fetch Results'}
                    </button>
                  </div>

                  {jobError && (
                    <div className="alert-neon alert-danger-neon">
                      <h6><FiAlertCircle size={11} style={{ marginRight: 4, verticalAlign: 'middle' }} />Error</h6>
                      {jobError}
                    </div>
                  )}
                  {jobInfo && (
                    <div className="alert-neon alert-info-neon" style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                      <FiInfo size={13} style={{ flexShrink: 0, marginTop: 2 }} />
                      <span>{jobInfo}</span>
                    </div>
                  )}

                  {jobStatus && (
                    <div className="status-section">
                      {statusUpdatedAt && <p className="status-timestamp">Last updated: {statusUpdatedAt.toLocaleString()}</p>}

                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                        <span style={{ fontSize: '0.78rem', color: 'var(--ink-muted)', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Status</span>
                        <span className={`status-pill ${getStatusClass(jobStatus.status)}`}>{jobStatus.status}</span>
                      </div>

                      {jobStatus.error && <p className="status-error-text"><strong>Error:</strong> {jobStatus.error}</p>}

                      {jobLogs.length > 0 && (
                        <>
                          <p style={{ fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-muted)', marginBottom: 0 }}>Logs</p>
                          <pre className="logs-terminal">{jobLogs.join('\n')}</pre>
                        </>
                      )}

                      {resultsError && <div className="alert-neon alert-warning-neon">{resultsError}</div>}
                      {resultsInfo && <div className="alert-neon alert-info-neon">{resultsInfo}</div>}

                      {resultsDownloadUrl && (
                        <div style={{ marginTop: '1rem' }}>
                          <a className="btn-neon btn-success-neon" href={resultsDownloadUrl} target="_blank" rel="noreferrer">
                            <FiDownload size={13} />
                            Download Results ZIP
                          </a>
                        </div>
                      )}

                      {jobResults.length > 0 && (
                        <div style={{ marginTop: '1rem' }}>
                          <p style={{ fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-muted)', marginBottom: '0.6rem' }}>Result Files</p>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {jobResults.map((result) => (
                              <button key={result.filename} type="button" className="btn-neon btn-success-neon" style={{ justifyContent: 'flex-start' }} onClick={() => downloadResultFile(result.filename, result.content_base64)}>
                                <FiDownload size={13} />
                                {result.filename}
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
    </div>
  );
};