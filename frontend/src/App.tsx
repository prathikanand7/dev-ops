import React, { useCallback, useEffect, useRef, useState, useMemo } from 'react';
import { BsMoon, BsSun } from 'react-icons/bs';
import {
  FiZap, FiRadio, FiLink, FiPlay, FiSearch, FiFileText,
  FiPackage, FiDownload, FiAlertCircle, FiInfo, FiCheckCircle,
  FiClock, FiChevronDown, FiChevronRight, FiRefreshCw, FiExternalLink,
} from 'react-icons/fi';
import { DropZone } from './components/DropZone';

/* ─── API types ─────────────────────────────────────────────── */
type RunResponse       = { message: string; job_id: string; execution_profile?: string; };
type JobStatusResponse = { job_id: string; job_name?: string; status: string; createdAt?: number; startedAt?: number; stoppedAt?: number; error?: string; };
type JobLogsResponse   = { job_id: string; logs: string[]; };
type JobResultsResponse = { job_id: string; status?: string; download_url?: string; results: Array<{ filename: string; content_base64: string; }>; };
type ThemeMode         = 'dark' | 'light';
type AppPage           = 'submission' | 'history';

/* ─── Param form types ──────────────────────────────────────── */
type ParamType  = 'number' | 'boolean' | 'string';
type ParamEntry = { value: string; type: ParamType; };
type FormParams = Record<string, ParamEntry>;

type JobHistoryItem = {
  jobId: string;
  submittedAt: string;
  notebookName: string;
  environmentName: string;
  executionProfile: string;
  params: Record<string, string>;
  status: string;
  logs: string;
  artifactUrl: string | null;
  s3Uri: string | null;
  info: string | null;
  error: string | null;
  lastCheckedAt: string | null;
};

const JOB_HISTORY_KEY = 'nop-job-history';

function detectType(v: string | number | boolean): ParamType {
  if (typeof v === 'number') return 'number';
  if (typeof v === 'boolean') return 'boolean';
  return 'string';
}

function isEnvironmentFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return name.endsWith('.yaml') || name.endsWith('.yml') || name.endsWith('.txt');
}

function safeLoadJobHistory(): JobHistoryItem[] {
  try {
    const raw = window.localStorage.getItem(JOB_HISTORY_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as JobHistoryItem[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function deriveS3Uri(downloadUrl: string): string | null {
  try {
    const parsed = new URL(downloadUrl);
    const host = parsed.hostname;
    const path = decodeURIComponent(parsed.pathname).replace(/^\/+/, '');
    if (!path) return null;

    const hostParts = host.split('.');
    if (hostParts.length > 0 && hostParts[0] && hostParts[0] !== 's3') {
      return `s3://${hostParts[0]}/${path}`;
    }

    const [bucket, ...rest] = path.split('/');
    if (!bucket || rest.length === 0) return null;
    return `s3://${bucket}/${rest.join('/')}`;
  } catch {
    return null;
  }
}

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<AppPage>('submission');

  /* Theme */
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const s = window.localStorage.getItem('nop-theme');
    if (s === 'dark' || s === 'light') return s;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  /* Connection */
  const [baseUrl, setBaseUrl] = useState('https://n69rb6bzvl.execute-api.eu-west-1.amazonaws.com/dev');
  const [apiKey,  setApiKey]  = useState('');

  /* Param form */
  const [formParams,      setFormParams]      = useState<FormParams>({});
  const [notebookLoaded,  setNotebookLoaded]  = useState(false);
  const [extractInfo,     setExtractInfo]     = useState<string | null>(null);

  /* Job submission */
  const [executionProfile, setExecutionProfile] = useState<'standard' | 'ec2_200gb'>('standard');
  /* FIX #5: files held in a ref as well so the submit button reads the latest value
     without needing a re-render cycle from the DropZone callback */
  const [files,        setFiles]        = useState<File[]>([]);
  const filesRef                        = useRef<File[]>([]);
  const [runResult,    setRunResult]    = useState<RunResponse | null>(null);
  const [runError,     setRunError]     = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  /* Job monitoring */
  const [jobId,              setJobId]              = useState('');
  const [jobStatus,          setJobStatus]          = useState<JobStatusResponse | null>(null);
  const [statusUpdatedAt,    setStatusUpdatedAt]    = useState<Date | null>(null);
  const [jobError,           setJobError]           = useState<string | null>(null);
  const [jobInfo,            setJobInfo]            = useState<string | null>(null);
  const [isChecking,         setIsChecking]         = useState(false);
  const [isFetchingLogs,     setIsFetchingLogs]     = useState(false);
  const [isFetchingResults,  setIsFetchingResults]  = useState(false);
  const [jobLogs,            setJobLogs]            = useState<string[]>([]);
  const [jobResults,         setJobResults]         = useState<JobResultsResponse['results']>([]);
  const [resultsDownloadUrl, setResultsDownloadUrl] = useState<string | null>(null);
  const [resultsError,       setResultsError]       = useState<string | null>(null);
  const [resultsInfo,        setResultsInfo]        = useState<string | null>(null);

  /* Job history */
  const [jobHistory, setJobHistory] = useState<JobHistoryItem[]>(() => safeLoadJobHistory());
  const [expandedHistory, setExpandedHistory] = useState<Record<string, boolean>>({});
  const [historyLoadingIds, setHistoryLoadingIds] = useState<Record<string, boolean>>({});
  const [historyError, setHistoryError] = useState<string | null>(null);

  const pollRef      = useRef<number | null>(null);
  const autoFetchRef = useRef<string | null>(null);

  const normalizedBaseUrl  = useMemo(() => baseUrl.replace(/\/$/, ''), [baseUrl]);
  const currentJobStatus   = jobStatus?.status || '';
  const logsReadyStatuses  = ['RUNNING', 'SUCCEEDED', 'FAILED'];
  const canFetchLogsNow    = logsReadyStatuses.includes(currentJobStatus);
  const canFetchResultsNow = currentJobStatus === 'SUCCEEDED';
  const hasParams          = Object.keys(formParams).length > 0;

  /* Derive disabled reason so we can show the user exactly what's missing */
  const hasNotebook = files.some((f) => f.name.toLowerCase().endsWith('.ipynb'));
  const hasEnvironmentFile = files.some((f) => isEnvironmentFile(f));
  const canSubmit   = !isSubmitting && !!apiKey && hasNotebook && hasEnvironmentFile;
  const submitHint  = !apiKey
    ? 'Enter your API key above to enable submission.'
    : !hasNotebook
    ? 'Drop a .ipynb notebook file to enable submission.'
    : !hasEnvironmentFile
    ? 'Drop an environment file (.yaml/.yml/.txt) to enable submission.'
    : null;

  /* ── lifecycle ──────────────────────────────────────────── */
  useEffect(() => () => { if (pollRef.current) window.clearInterval(pollRef.current); }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    window.localStorage.setItem('nop-theme', theme);
  }, [theme]);

  useEffect(() => {
    window.localStorage.setItem(JOB_HISTORY_KEY, JSON.stringify(jobHistory.slice(0, 200)));
  }, [jobHistory]);

  useEffect(() => {
    if (!jobId || !apiKey) return;
    if (jobStatus?.status !== 'SUCCEEDED') return;
    if (resultsDownloadUrl || isFetchingResults) return;
    if (autoFetchRef.current === jobId) return;
    autoFetchRef.current = jobId;
    void handleFetchResults();
  }, [jobId, apiKey, jobStatus?.status, resultsDownloadUrl, isFetchingResults]);

  /* ── utils ──────────────────────────────────────────────── */
  function decodeApiBody<T>(raw: unknown): T {
    if (typeof raw === 'string') { try { return JSON.parse(raw) as T; } catch { throw new Error(`Non-JSON: ${raw}`); } }
    return raw as T;
  }

  function readFileAsText(file: File): Promise<string> {
    return new Promise((res, rej) => {
      const r = new FileReader();
      r.onload  = () => { if (typeof r.result !== 'string') { rej(new Error('Not text')); return; } res(r.result); };
      r.onerror = () => rej(r.error || new Error('Read failed'));
      r.readAsText(file);
    });
  }

  function sleep(ms: number) { return new Promise<void>((r) => window.setTimeout(r, ms)); }

  function upsertHistoryItem(item: JobHistoryItem) {
    setJobHistory((prev) => [item, ...prev.filter((h) => h.jobId !== item.jobId)].slice(0, 200));
  }

  function patchHistoryItem(jobIdToPatch: string, patch: Partial<JobHistoryItem>) {
    setJobHistory((prev) => prev.map((h) => (
      h.jobId === jobIdToPatch ? { ...h, ...patch } : h
    )));
  }

  async function refreshHistoryItem(targetJobId: string, includeLogs: boolean): Promise<void> {
    if (!targetJobId.trim()) return;
    setHistoryError(null);
    setHistoryLoadingIds((prev) => ({ ...prev, [targetJobId]: true }));

    try {
      const statusRes = await fetch(`${normalizedBaseUrl}/batch/jobs/${targetJobId}`, {
        headers: { 'x-api-key': apiKey },
      });
      if (!statusRes.ok) {
        const t = await statusRes.text();
        patchHistoryItem(targetJobId, { error: `Status failed (${statusRes.status}): ${t}` });
        return;
      }
      const statusData = decodeApiBody<JobStatusResponse>((await statusRes.json()) as unknown);
      const patch: Partial<JobHistoryItem> = {
        status: statusData.status,
        error: null,
        info: null,
        lastCheckedAt: new Date().toISOString(),
      };

      if (includeLogs) {
        if (!logsReadyStatuses.includes(statusData.status)) {
          patch.logs = 'Logs available once status is RUNNING.';
        } else {
          const logsRes = await fetch(`${normalizedBaseUrl}/batch/jobs/${targetJobId}/logs`, {
            headers: { 'x-api-key': apiKey },
          });
          if (logsRes.ok) {
            const logsData = decodeApiBody<JobLogsResponse>((await logsRes.json()) as unknown);
            patch.logs = (logsData.logs || []).join('\n');
          } else {
            const t = await logsRes.text();
            patch.error = `Logs failed (${logsRes.status}): ${t}`;
          }
        }
      }

      if (statusData.status === 'SUCCEEDED') {
        const resultsRes = await fetch(`${normalizedBaseUrl}/batch/jobs/${targetJobId}/results`, {
          headers: { 'x-api-key': apiKey },
        });
        if (resultsRes.ok) {
          const resultsData = decodeApiBody<JobResultsResponse>((await resultsRes.json()) as unknown);
          if (resultsData.download_url) {
            patch.artifactUrl = resultsData.download_url;
            patch.s3Uri = deriveS3Uri(resultsData.download_url);
          }
        }
      }

      patchHistoryItem(targetJobId, patch);
    } catch (err) {
      setHistoryError((err as Error).message);
    } finally {
      setHistoryLoadingIds((prev) => {
        const next = { ...prev };
        delete next[targetJobId];
        return next;
      });
    }
  }

  async function refreshAllHistoryItems(): Promise<void> {
    if (!apiKey || jobHistory.length === 0) return;
    for (const item of jobHistory) {
      // Sequential refresh is gentler on API Gateway and CloudWatch APIs.
      // eslint-disable-next-line no-await-in-loop
      await refreshHistoryItem(item.jobId, false);
    }
  }

  /* ── notebook param extraction ──────────────────────────── */
  function parseNotebookParameters(text: string): Record<string, string | number | boolean> {
    const nb = JSON.parse(text) as {
      cells?: Array<{ cell_type?: string; metadata?: { tags?: string[] }; source?: string[] }>;
    };
    const fallbackCellRegex = /^\s*((?:param_|conf_)[A-Za-z0-9_]*)\s*(?:<-|=)\s*(.+?)\s*$/;
    function stripComment(line: string): string {
      let inString: string | null = null;
      for (let index = 0; index < line.length; index += 1) {
        const char = line[index];
        if (inString) {
          if (char === inString) inString = null;
          continue;
        }
        if (char === '"' || char === "'") {
          inString = char;
          continue;
        }
        if (char === '#') {
          return line.slice(0, index).trimEnd();
        }
      }
      return line;
    }

    let cell = nb.cells?.find(
      (c) => c.cell_type === 'code' && Array.isArray(c.metadata?.tags) && c.metadata!.tags!.includes('parameters'),
    );
    if (!cell) {
      cell = nb.cells?.find(
        (c) => c.cell_type === 'code' && c.source?.some((line) => fallbackCellRegex.test(stripComment(line))),
      );
    }
    if (!cell?.source?.length) return {};
    const out: Record<string, string | number | boolean> = {};
    const re  = /^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:<-|=)\s*(.+?)\s*$/;
    cell.source.forEach((raw) => {
      const line = stripComment(raw).trim();
      if (!line || line.startsWith('#')) return;
      const m = line.match(re);
      if (!m) return;
      const [, key, vRaw] = m;
      let v: string | number | boolean = vRaw;
      if (/^[-+]?\d+(?:\.\d+)?$/.test(vRaw)) {
        v = Number(vRaw);
      } else if (/^(true|false)$/i.test(vRaw)) {
        // unquoted: true / false / True / False
        v = vRaw.toLowerCase() === 'true';
      } else {
        // strip surrounding quotes first, then re-check for boolean
        const stripped = vRaw.replace(/^['"]|['"]$/g, '');
        if (/^(true|false)$/i.test(stripped)) {
          v = stripped.toLowerCase() === 'true';
        } else {
          v = stripped;
        }
      }
      out[key] = v;
    });
    return out;
  }

  async function extractParametersFromNotebook(file: File): Promise<void> {
    try {
      const text      = await readFileAsText(file);
      const extracted = parseNotebookParameters(text);
      setNotebookLoaded(true);
      if (Object.keys(extracted).length === 0) {
        setFormParams({});
        setExtractInfo('Notebook loaded — no tagged parameters cell found.');
        return;
      }
      const fp: FormParams = {};
      Object.entries(extracted).forEach(([k, v]) => { fp[k] = { value: String(v), type: detectType(v) }; });
      setFormParams(fp);
      setExtractInfo(`${Object.keys(fp).length} parameter${Object.keys(fp).length !== 1 ? 's' : ''} extracted from notebook.`);
    } catch (err) {
      setNotebookLoaded(true);
      setFormParams({});
      setExtractInfo(`Could not parse notebook: ${(err as Error).message}`);
    }
  }

  /* FIX #5: useCallback so DropZone's useEffect([files, onFilesChange])
     does NOT re-fire every time App re-renders, which would reset files state */
  const handleFilesChange = useCallback(async (newFiles: File[]): Promise<void> => {
    /* Keep ref in sync for immediate reads (e.g. submit button) */
    filesRef.current = newFiles;
    setFiles(newFiles);
    const nb = newFiles.find((f) => f.name.toLowerCase().endsWith('.ipynb'));
    if (nb) {
      await extractParametersFromNotebook(nb);
    } else {
      setNotebookLoaded(false);
      setFormParams({});
      setExtractInfo(null);
    }
  /* eslint-disable-next-line react-hooks/exhaustive-deps */
  }, []); // intentionally empty — extractParametersFromNotebook uses no captured state

  /* FIX #4: update a single param value (user edits an auto-filled field) */
  function updateParam(key: string, value: string) {
    setFormParams((prev) => ({ ...prev, [key]: { ...prev[key], value } }));
  }

  /* ── submit ─────────────────────────────────────────────── */
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    /* Read from ref to get latest file list regardless of render cycle */
    const currentFiles = filesRef.current;

    setRunError(null); setRunResult(null); setJobError(null); setJobInfo(null);
    setJobStatus(null); setJobLogs([]); setJobResults([]);
    setResultsDownloadUrl(null); setResultsError(null); setResultsInfo(null);
    autoFetchRef.current = null;
    setIsSubmitting(true);

    try {
      const nb = currentFiles.find((f) => f.name.toLowerCase().endsWith('.ipynb'));
      if (!nb) { setRunError('You must include one .ipynb notebook file.'); return; }

      const envFile = currentFiles.find((f) => isEnvironmentFile(f));
      if (!envFile) { setRunError('You must include an environment file (.yaml, .yml, or .txt).'); return; }

      const formData = new FormData();
      formData.append('notebook', nb, nb.name);
      formData.append('environment', envFile, envFile.name);

      /* FIX #4: use current formParams values (whatever the user has edited) */
      Object.entries(formParams).forEach(([key, entry]) => {
        if (key.trim()) formData.append(key, entry.value);
      });

      formData.append('execution_profile', executionProfile);

      /* Append extra data files (exclude notebook and chosen environment file) */
      let uploadIndex = 0;
      currentFiles
        .filter((f) => !f.name.toLowerCase().endsWith('.ipynb') && f !== envFile)
        .forEach((file) => {
          formData.append(uploadIndex === 0 ? 'upload_data' : `upload_${String(uploadIndex).padStart(2, '0')}`, file);
          uploadIndex += 1;
        });

      const res = await fetch(`${normalizedBaseUrl}/batch/jobs`, {
        method: 'POST', headers: { 'x-api-key': apiKey }, body: formData,
      });
      if (!res.ok) { const t = await res.text(); setRunError(`Request failed (${res.status}): ${t}`); return; }
      const data = decodeApiBody<RunResponse>((await res.json()) as unknown);
      const envName = envFile.name;
      const paramsSnapshot: Record<string, string> = {};
      Object.entries(formParams).forEach(([k, v]) => { paramsSnapshot[k] = v.value; });

      upsertHistoryItem({
        jobId: data.job_id,
        submittedAt: new Date().toISOString(),
        notebookName: nb.name,
        environmentName: envName,
        executionProfile,
        params: paramsSnapshot,
        status: 'SUBMITTED',
        logs: '',
        artifactUrl: null,
        s3Uri: null,
        info: null,
        error: null,
        lastCheckedAt: null,
      });

      setRunResult(data); setJobId(data.job_id); startPolling(data.job_id);
    } catch (err) {
      setRunError((err as Error).message);
    } finally {
      setIsSubmitting(false);
    }
  }

  /* ── status / logs / results ────────────────────────────── */
  async function fetchStatus(id: string, opts?: { suppressError?: boolean }): Promise<JobStatusResponse | null> {
    const sup = opts?.suppressError ?? false;
    if (!sup) setJobError(null);
    try {
      const res = await fetch(`${normalizedBaseUrl}/batch/jobs/${id}`, { headers: { 'x-api-key': apiKey } });
      if (!res.ok) { const t = await res.text(); if (!sup) setJobError(`Request failed (${res.status}): ${t}`); return null; }
      const data = decodeApiBody<JobStatusResponse>((await res.json()) as unknown);
      setJobStatus(data); setStatusUpdatedAt(new Date());
      patchHistoryItem(data.job_id, { status: data.status, lastCheckedAt: new Date().toISOString(), error: null });
      return data;
    } catch (err) { if (!sup) setJobError((err as Error).message); return null; }
  }

  async function handleCheckStatus(e: React.FormEvent) {
    e.preventDefault(); setIsChecking(true); setJobInfo(null);
    try { await fetchStatus(jobId); } finally { setIsChecking(false); }
  }

  function startPolling(id: string) {
    if (pollRef.current) window.clearInterval(pollRef.current);
    pollRef.current = window.setInterval(async () => {
      const s = await fetchStatus(id);
      if (s && ['SUCCEEDED', 'FAILED'].includes(s.status)) {
        if (pollRef.current) { window.clearInterval(pollRef.current); pollRef.current = null; }
      }
    }, 10000);
  }

  async function handleFetchLogs() {
    if (!jobId.trim()) return;
    setIsFetchingLogs(true); setJobError(null); setJobInfo(null);
    /* Clear results panel so view switches cleanly to logs */
    setResultsInfo(null); setResultsError(null); setJobResults([]); setResultsDownloadUrl(null);
    try {
      const s = (await fetchStatus(jobId, { suppressError: true })) || jobStatus;
      if (!logsReadyStatuses.includes(s?.status || '')) { setJobLogs([]); setJobInfo('Logs available once status is RUNNING.'); return; }
      const res = await fetch(`${normalizedBaseUrl}/batch/jobs/${jobId}/logs`, { headers: { 'x-api-key': apiKey } });
      if (!res.ok) {
        const t = await res.text();
        if (res.status === 500 && /log stream does not exist/i.test(t)) { setJobInfo('Log stream not ready yet. Try again shortly.'); return; }
        setJobError(`Logs request failed (${res.status}): ${t}`); return;
      }
      const data = decodeApiBody<JobLogsResponse>((await res.json()) as unknown);
      setJobLogs(data.logs || []);
      patchHistoryItem(jobId, { logs: (data.logs || []).join('\n'), info: null, error: null });
    } catch (err) { setJobError((err as Error).message); }
    finally { setIsFetchingLogs(false); }
  }

  async function handleFetchResults() {
    if (!jobId.trim()) return;
    setIsFetchingResults(true); setResultsError(null); setResultsInfo(null); setResultsDownloadUrl(null);
    /* Clear logs panel so view switches cleanly to results */
    setJobInfo(null); setJobLogs([]);
    try {
      const s = (await fetchStatus(jobId, { suppressError: true })) || jobStatus;
      if (s?.status !== 'SUCCEEDED') { setJobResults([]); setResultsInfo('Results available only after SUCCEEDED status.'); return; }
      for (let attempt = 1; attempt <= 8; attempt++) {
        const res = await fetch(`${normalizedBaseUrl}/batch/jobs/${jobId}/results`, { headers: { 'x-api-key': apiKey } });
        if (!res.ok) {
          const t = await res.text();
          if (res.status === 404 && attempt < 8) { setResultsInfo(`Preparing ZIP... (${attempt}/8)`); await sleep(2500); continue; }
          if (res.status === 404) { setResultsInfo('Results still being packaged. Try again shortly.'); return; }
          setResultsError(`Results failed (${res.status}): ${t}`); return;
        }
        const data = decodeApiBody<JobResultsResponse>((await res.json()) as unknown);
        if (data.download_url) {
          setJobResults([]); setResultsDownloadUrl(data.download_url); setResultsInfo('Results ZIP ready.');
          patchHistoryItem(jobId, {
            artifactUrl: data.download_url,
            s3Uri: deriveS3Uri(data.download_url),
            status: 'SUCCEEDED',
            info: 'Results ZIP ready.',
            error: null,
          });
          return;
        }
        if (Array.isArray(data.results) && data.results.length > 0) { setResultsDownloadUrl(null); setJobResults(data.results); return; }
        if (attempt < 8) { setResultsInfo(`Waiting for results... (${attempt}/8)`); await sleep(2500); continue; }
        setResultsInfo('Results URL not ready yet. Please try again shortly.');
      }
    } catch (err) { setResultsError((err as Error).message); }
    finally { setIsFetchingResults(false); }
  }

  function downloadResultFile(filename: string, b64: string) {
    const bytes = window.atob(b64);
    const arr   = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
    const url = URL.createObjectURL(new Blob([arr]));
    const a   = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  }

  function toggleTheme() { setTheme((p) => (p === 'dark' ? 'light' : 'dark')); }

  function getStatusClass(s: string) {
    if (s === 'SUCCEEDED') return 'status-succeeded';
    if (s === 'FAILED')    return 'status-failed';
    if (s === 'RUNNING')   return 'status-running';
    return 'status-other';
  }

  /* ── param field renderer ───────────────────────────────── */
  /* FIX #4: fields are fully controlled — onChange calls updateParam */
  function renderParamField(key: string, entry: ParamEntry) {
    return (
      <div key={key} className="form-group" style={{ marginBottom: 0 }}>
        {/* title shows full name on hover when label is truncated */}
        <label className="param-field-label" htmlFor={`param-${key}`} title={key}>
          <span className="param-field-key">{key}</span>
          <span className={`param-type-tag param-type-${entry.type}`}>{entry.type}</span>
        </label>

        {entry.type === 'boolean' ? (
          <select
            id={`param-${key}`}
            className="form-control-styled"
            value={entry.value}
            onChange={(e) => updateParam(key, e.target.value)}
          >
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        ) : (
          <input
            id={`param-${key}`}
            type={entry.type === 'number' ? 'number' : 'text'}
            className="form-control-styled"
            value={entry.value}
            onChange={(e) => updateParam(key, e.target.value)}
            step={entry.type === 'number' ? 'any' : undefined}
          />
        )}
      </div>
    );
  }

  /* ── render ─────────────────────────────────────────────── */
  return (
    <div className="app-root">

      {/* Background */}
      <div className="app-bg" aria-hidden="true">
        <div className="app-bg-grid" />
        <div className="app-bg-lines" />
        <div className="app-bg-corner-tl" />
        <div className="app-bg-corner-br" />
        <div className="app-bg-bulb" />
        <div className="app-bg-bulb-core" />
      </div>

      {/* Navbar */}
      <nav className="app-navbar">
        <div className="navbar-inner">
          <div className="navbar-brand-area">
            <div className="navbar-logo-dot" aria-hidden="true" />
            <span className="navbar-brand">Notebook<span>Ops</span></span>
          </div>

          <div className="navbar-tabs" role="tablist" aria-label="Page navigation">
            <button
              type="button"
              role="tab"
              aria-selected={activePage === 'submission'}
              className={`navbar-tab-btn ${activePage === 'submission' ? 'is-active' : ''}`}
              onClick={() => setActivePage('submission')}
            >
              Job Submission
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activePage === 'history'}
              className={`navbar-tab-btn ${activePage === 'history' ? 'is-active' : ''}`}
              onClick={() => setActivePage('history')}
            >
              Job History
            </button>
          </div>

          <button type="button" className="theme-toggle-btn" onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>
            {theme === 'dark' ? <BsSun size={13} /> : <BsMoon size={13} />}
            {theme === 'dark' ? 'Light' : 'Dark'}
          </button>
        </div>
      </nav>

      {/* Page */}
      <div className="page-container">
        {activePage === 'submission' ? (
          <>

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

        {/* Two columns — FIX #1: align-items: start prevents forced equal heights */}
        <div className="row-grid row-grid-2">

          {/* ── Submit Job ── */}
          <div className="glass-card">
            <div className="card-inner">
              <div className="card-head">
                <div className="card-head-icon"><FiZap size={14} /></div>
                <h5>Trigger Notebook Run</h5>
              </div>
              <div className="card-body-inner">
                <form onSubmit={handleSubmit}>

                  {/* Drop zone */}
                  <div className="form-group">
                    <DropZone
                      label="Upload Files"
                      onFilesChange={handleFilesChange}
                    />
                    <p className="submit-hint">
                      <FiInfo size={15} style={{ marginRight: 4, verticalAlign: 'middle' }} />
                      One .ipynb notebook & one environment file (.yaml/.yml/.txt) are needed. Data files (.xlsx/.xls) are optional.
                    </p>
                    {extractInfo && (
                      <p className="extract-info" style={{ marginTop: '0.55rem' }}>
                        <FiInfo size={11} />{extractInfo}
                      </p>
                    )}
                  </div>

                  {/* Parameters */}
                  <div className="form-group">
                    <label className="form-label-styled">Parameters</label>

                    {/* FIX #2: info row instead of dashed dropzone box */}
                    {!notebookLoaded ? (
                      <div className="param-pending">
                        <FiInfo size={14} />
                        <span>Drop a notebook above, parameters will be auto-extracted and shown here as editable fields.</span>
                      </div>
                    ) : !hasParams ? (
                      <div className="param-no-params">
                        <FiInfo size={14} />
                        <span>No tagged parameters cell found in this notebook.</span>
                      </div>
                    ) : (
                      /* FIX #4: fully controlled inputs — changes go to formParams state */
                      <div className="param-form-grid">
                        {Object.entries(formParams).map(([key, entry]) => renderParamField(key, entry))}
                      </div>
                    )}
                  </div>

                  {/* Execution profile — FIX #3: option colours set via CSS */}
                  <div className="form-group">
                    <label className="form-label-styled" htmlFor="execution-profile">Execution Profile</label>
                    <select
                      id="execution-profile"
                      className="form-control-styled"
                      value={executionProfile}
                      onChange={(e) => setExecutionProfile(e.target.value as 'standard' | 'ec2_200gb')}
                    >
                      <option value="standard">Standard</option>
                      <option value="ec2_200gb">Large EC2 (200 GB)</option>
                    </select>
                    <p className="form-hint">Use <code>ec2_200gb</code> for high-storage workloads.</p>
                  </div>

                  {/* FIX #5: button enabled as soon as notebook + apiKey present */}
                  <div className="btn-row">
                    <button
                      type="submit"
                      className="btn-neon btn-primary-neon"
                      disabled={!canSubmit}
                    >
                      <FiPlay size={13} />
                      {isSubmitting ? 'Submitting…' : 'Submit Job'}
                    </button>
                  </div>

                  {/* Show the user exactly why the button is disabled */}
                  {submitHint && (
                    <p className="submit-hint">
                      <FiInfo size={12} />
                      {submitHint}
                    </p>
                  )}

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

          {/* ── Job Status ── */}
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
                    <input
                      id="job-id"
                      type="text"
                      className="form-control-styled"
                      value={jobId}
                      onChange={(e) => setJobId(e.target.value)}
                      placeholder="Paste Job ID from the left panel"
                      required
                    />
                    {runResult && (
                      <p className="form-hint">Auto-filled from submission: <code>{runResult.job_id.substring(0, 8)}…</code></p>
                    )}
                  </div>

                  <div className="btn-row">
                    <button type="submit" className="btn-neon btn-secondary-neon" disabled={isChecking || !apiKey || !jobId}>
                      <FiSearch size={13} />{isChecking ? 'Checking…' : 'Check Status'}
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

                  {/* Fix 1: single info area — shows jobInfo OR resultsInfo, whichever is active */}
                  {(jobInfo || resultsInfo) && (
                    <div className="alert-neon alert-info-neon" style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                      <FiInfo size={13} style={{ flexShrink: 0, marginTop: 2 }} />
                      <span>{resultsInfo || jobInfo}</span>
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

                      {resultsDownloadUrl && (
                        <div style={{ marginTop: '1rem' }}>
                          <a className="btn-neon btn-success-neon" href={resultsDownloadUrl} target="_blank" rel="noreferrer">
                            <FiDownload size={13} />Download Results ZIP
                          </a>
                        </div>
                      )}

                      {jobResults.length > 0 && (
                        <div style={{ marginTop: '1rem' }}>
                          <p style={{ fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-muted)', marginBottom: '0.6rem' }}>Result Files</p>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {jobResults.map((r) => (
                              <button key={r.filename} type="button" className="btn-neon btn-success-neon"
                                style={{ justifyContent: 'flex-start' }}
                                onClick={() => downloadResultFile(r.filename, r.content_base64)}>
                                <FiDownload size={13} />{r.filename}
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
          </>
        ) : (
          <div className="row-grid">
            <div className="glass-card">
              <div className="card-inner">
                <div className="card-head">
                  <div className="card-head-icon"><FiClock size={14} /></div>
                  <h5>Job History</h5>
                </div>
                <div className="card-body-inner">
                  <div className="history-actions-row">
                    <p className="form-hint" style={{ margin: 0 }}>
                      Scroll, expand, and inspect historical runs with parameters, logs, and artifact links.
                    </p>
                    <button
                      type="button"
                      className="btn-neon btn-ghost-neon"
                      onClick={() => void refreshAllHistoryItems()}
                      disabled={!apiKey || Object.keys(historyLoadingIds).length > 0 || jobHistory.length === 0}
                    >
                      <FiRefreshCw size={13} />Refresh All
                    </button>
                  </div>

                  {historyError && (
                    <div className="alert-neon alert-warning-neon" style={{ marginTop: '0.9rem' }}>{historyError}</div>
                  )}

                  {jobHistory.length === 0 ? (
                    <div className="param-pending" style={{ marginTop: '0.95rem' }}>
                      <FiInfo size={14} />
                      <span>No jobs in history yet. Submit a job from Job Submission and it will appear here.</span>
                    </div>
                  ) : (
                    <div className="history-scroll-list">
                      {jobHistory.map((item) => {
                        const isExpanded = !!expandedHistory[item.jobId];
                        const isLoading = !!historyLoadingIds[item.jobId];
                        const hasParamsForItem = Object.keys(item.params || {}).length > 0;
                        return (
                          <div key={item.jobId} className="history-item-card">
                            <div className="history-item-top">
                              <div>
                                <p className="history-item-jobid">{item.jobId}</p>
                                <p className="history-item-meta">
                                  Submitted {new Date(item.submittedAt).toLocaleString()}
                                  {item.lastCheckedAt ? ` • Checked ${new Date(item.lastCheckedAt).toLocaleString()}` : ''}
                                </p>
                              </div>

                              <div className="history-item-top-right">
                                <span className={`status-pill ${getStatusClass(item.status)}`}>{item.status}</span>
                                <button
                                  type="button"
                                  className="btn-neon btn-ghost-neon"
                                  onClick={() => void refreshHistoryItem(item.jobId, isExpanded)}
                                  disabled={!apiKey || isLoading}
                                >
                                  <FiRefreshCw size={13} />{isLoading ? 'Refreshing…' : 'Refresh'}
                                </button>
                                <button
                                  type="button"
                                  className="btn-neon btn-secondary-neon"
                                  onClick={() => {
                                    setExpandedHistory((prev) => ({ ...prev, [item.jobId]: !isExpanded }));
                                    if (!isExpanded) void refreshHistoryItem(item.jobId, true);
                                  }}
                                >
                                  {isExpanded ? <FiChevronDown size={13} /> : <FiChevronRight size={13} />}
                                  {isExpanded ? 'Collapse' : 'Expand'}
                                </button>
                              </div>
                            </div>

                            {isExpanded && (
                              <div className="history-item-expanded">
                                <div className="history-kv-grid">
                                  <div className="history-kv-box">
                                    <span className="history-kv-label">Notebook</span>
                                    <span className="history-kv-value">{item.notebookName || '-'}</span>
                                  </div>
                                  <div className="history-kv-box">
                                    <span className="history-kv-label">Environment</span>
                                    <span className="history-kv-value">{item.environmentName || '-'}</span>
                                  </div>
                                  <div className="history-kv-box">
                                    <span className="history-kv-label">Profile</span>
                                    <span className="history-kv-value">{item.executionProfile || '-'}</span>
                                  </div>
                                  <div className="history-kv-box">
                                    <span className="history-kv-label">S3 Prefix</span>
                                    <span className="history-kv-value">jobs/{item.jobId}/</span>
                                  </div>
                                </div>

                                {item.artifactUrl && (
                                  <div className="history-artifact-row">
                                    <a className="btn-neon btn-success-neon" href={item.artifactUrl} target="_blank" rel="noreferrer">
                                      <FiExternalLink size={13} />Open Artifact Link
                                    </a>
                                    {item.s3Uri && <span className="history-s3-link">{item.s3Uri}</span>}
                                  </div>
                                )}

                                <div style={{ marginTop: '0.8rem' }}>
                                  <p className="history-subtitle">Parameters</p>
                                  {!hasParamsForItem ? (
                                    <p className="form-hint" style={{ marginTop: 0 }}>No parameters captured for this run.</p>
                                  ) : (
                                    <div className="history-params-grid">
                                      {Object.entries(item.params).map(([paramKey, paramValue]) => (
                                        <div key={paramKey} className="history-param-row">
                                          <span className="history-param-key">{paramKey}</span>
                                          <span className="history-param-value">{paramValue}</span>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>

                                <div style={{ marginTop: '0.8rem' }}>
                                  <p className="history-subtitle">Logs</p>
                                  <pre className="logs-terminal history-logs-terminal">{item.logs || 'No logs loaded yet. Click Refresh.'}</pre>
                                </div>

                                {(item.info || item.error) && (
                                  <div className={`alert-neon ${item.error ? 'alert-danger-neon' : 'alert-info-neon'}`} style={{ marginTop: '0.8rem' }}>
                                    {item.error || item.info}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};