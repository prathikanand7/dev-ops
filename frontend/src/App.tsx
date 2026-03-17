import React, { useCallback, useEffect, useRef, useState, useMemo } from 'react';
import { BsMoon, BsSun } from 'react-icons/bs';
import { ParamsModal } from './components/job_history/ParamsModal';
import { LogsModal } from './components/job_history/LogsModal';
import { ApiConnectionCard } from './components/job_submission/ApiConnectionCard';
import { SubmitJobCard } from './components/job_submission/SubmitJobCard';
import { JobStatusCard } from './components/job_submission/JobStatusCard';
import { JobHistoryTable } from './components/job_history/JobHistoryTable';
import {
  DEFAULT_EXECUTION_PROFILE,
  EXECUTION_PROFILE_OPTIONS,
  JOB_PROFILE_CURRENCY,
  getExecutionProfile,
} from './config/jobProfiles';
import type {
  RunResponse, JobStatusResponse, JobLogsResponse, JobResultsResponse,
  ThemeMode, AppPage, ParamEntry, FormParams, SubmissionDraft,
  JobHistoryItem, JobHistoryListResponse,
} from './types';
import { SUBMISSION_DRAFT_KEY, detectType, isEnvironmentFile, normalizeHistoryItem, safeLoadSubmissionDraft } from './utils/storage';
import { decodeApiBody, deriveS3Uri } from './utils/api';
import { readFileAsText, parseNotebookParameters, downloadResultFile } from './utils/notebook';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<AppPage>('submission');
  const submissionDraftRef = useRef<SubmissionDraft>(safeLoadSubmissionDraft());

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
  const [executionProfile, setExecutionProfile] = useState<string>(() => submissionDraftRef.current.executionProfile || DEFAULT_EXECUTION_PROFILE);
  const [files,        setFiles]        = useState<File[]>([]);
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
  const [jobHistory, setJobHistory] = useState<JobHistoryItem[]>([]);
  const [historyLoadingIds, setHistoryLoadingIds] = useState<Record<string, boolean>>({});
  const [historyListLoading, setHistoryListLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [logsLoadingJobIds, setLogsLoadingJobIds] = useState<Record<string, boolean>>({});
  const [artifactHydratingJobIds, setArtifactHydratingJobIds] = useState<Record<string, boolean>>({});
  const [activeLogsJobId, setActiveLogsJobId] = useState<string | null>(null);
  const [activeParamsJobId, setActiveParamsJobId] = useState<string | null>(null);

  const pollRef      = useRef<number | null>(null);
  const autoFetchRef = useRef<string | null>(null);

  const normalizedBaseUrl  = useMemo(() => baseUrl.replace(/\/$/, ''), [baseUrl]);
  const currentJobStatus   = jobStatus?.status || '';
  const logsReadyStatuses  = ['RUNNING', 'SUCCEEDED', 'FAILED'];
  const canFetchLogsNow    = logsReadyStatuses.includes(currentJobStatus);
  const canFetchResultsNow = currentJobStatus === 'SUCCEEDED';
  const hasParams          = Object.keys(formParams).length > 0;
  const activeLogsItem     = useMemo(
    () => jobHistory.find((item) => item.jobId === activeLogsJobId) || null,
    [jobHistory, activeLogsJobId],
  );
  const activeParamsItem   = useMemo(
    () => jobHistory.find((item) => item.jobId === activeParamsJobId) || null,
    [jobHistory, activeParamsJobId],
  );
  const selectedExecutionProfile = useMemo(
    () => getExecutionProfile(executionProfile) ?? getExecutionProfile(DEFAULT_EXECUTION_PROFILE),
    [executionProfile],
  );

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
    const draft: SubmissionDraft = {
      formParams,
      notebookLoaded,
      extractInfo,
      executionProfile,
    };
    window.localStorage.setItem(SUBMISSION_DRAFT_KEY, JSON.stringify(draft));
  }, [formParams, notebookLoaded, extractInfo, executionProfile]);

  useEffect(() => {
    if (!jobId || !apiKey) return;
    if (jobStatus?.status !== 'SUCCEEDED') return;
    if (resultsDownloadUrl || isFetchingResults) return;
    if (autoFetchRef.current === jobId) return;
    autoFetchRef.current = jobId;
    void handleFetchResults();
  }, [jobId, apiKey, jobStatus?.status, resultsDownloadUrl, isFetchingResults]);

  useEffect(() => {
    if (activePage !== 'history') return;
    if (!apiKey) {
      setJobHistory([]);
      setHistoryError(null);
      return;
    }
    void fetchHistoryList();
  }, [activePage, apiKey, normalizedBaseUrl]);

  useEffect(() => {
    if (!activeParamsJobId) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setActiveParamsJobId(null);
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeParamsJobId]);

  useEffect(() => {
    if (!activeLogsJobId) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setActiveLogsJobId(null);
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeLogsJobId]);

  /* ── utils ──────────────────────────────────────────────── */
  function sleep(ms: number) { return new Promise<void>((r) => window.setTimeout(r, ms)); }

  async function copyTextToClipboard(text: string): Promise<boolean> {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        return true;
      }
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      const ok = document.execCommand('copy');
      document.body.removeChild(ta);
      return ok;
    } catch {
      return false;
    }
  }

  async function copyHistoryJobId(jobIdToCopy: string): Promise<void> {
    const copied = await copyTextToClipboard(jobIdToCopy);
    patchHistoryItem(jobIdToCopy, {
      info: copied ? 'Job ID copied to clipboard.' : null,
      error: copied ? null : 'Failed to copy Job ID.',
    });
  }

  function upsertHistoryItem(item: JobHistoryItem) {
    setJobHistory((prev) => [item, ...prev.filter((h) => h.jobId !== item.jobId)].slice(0, 200));
  }

  function patchHistoryItem(jobIdToPatch: string, patch: Partial<JobHistoryItem>) {
    setJobHistory((prev) => prev.map((h) => (
      h.jobId === jobIdToPatch ? { ...h, ...patch } : h
    )));
  }

  async function hydrateHistoryArtifacts(items: JobHistoryItem[]): Promise<void> {
    const candidates = items.filter((item) => item.status === 'SUCCEEDED' && !item.artifactUrl);
    if (candidates.length === 0) return;

    setArtifactHydratingJobIds((prev) => {
      const next = { ...prev };
      candidates.forEach((item) => {
        next[item.jobId] = true;
      });
      return next;
    });

    try {
      const results = await Promise.all(candidates.map(async (item) => {
        try {
          const res = await fetch(`${normalizedBaseUrl}/batch/jobs/${item.jobId}/results`, {
            headers: { 'x-api-key': apiKey },
          });
          if (!res.ok) return null;
          const data = decodeApiBody<JobResultsResponse>((await res.json()) as unknown);
          if (!data.download_url) return null;
          return {
            jobId: item.jobId,
            artifactUrl: data.download_url,
            s3Uri: deriveS3Uri(data.download_url),
          };
        } catch {
          return null;
        }
      }));

      const patches = results.filter((result): result is { jobId: string; artifactUrl: string; s3Uri: string | null } => !!result);
      if (patches.length === 0) return;

      const patchMap = new Map(patches.map((patch) => [patch.jobId, patch]));
      setJobHistory((prev) => prev.map((item) => {
        const patch = patchMap.get(item.jobId);
        if (!patch) return item;
        return {
          ...item,
          artifactUrl: patch.artifactUrl,
          s3Uri: patch.s3Uri,
        };
      }));
    } finally {
      setArtifactHydratingJobIds((prev) => {
        const next = { ...prev };
        candidates.forEach((item) => {
          delete next[item.jobId];
        });
        return next;
      });
    }
  }

  async function fetchHistoryList(): Promise<void> {
    if (!apiKey) return;
    setHistoryListLoading(true);
    setHistoryError(null);
    try {
      const res = await fetch(`${normalizedBaseUrl}/batch/jobs/history_list`, {
        headers: { 'x-api-key': apiKey },
      });
      if (!res.ok) {
        const t = await res.text();
        setHistoryError(`History list failed (${res.status}): ${t}`);
        return;
      }
      const body = decodeApiBody<JobHistoryListResponse>((await res.json()) as unknown);
      const mapped = (body.jobs || [])
        .map((item) => normalizeHistoryItem(item as Partial<JobHistoryItem> & Record<string, unknown>))
        .filter((item) => item.jobId);
      setJobHistory(mapped);
      void hydrateHistoryArtifacts(mapped);
    } catch (err) {
      setHistoryError((err as Error).message);
    } finally {
      setHistoryListLoading(false);
    }
  }

  async function refreshHistoryItem(targetJobId: string, includeLogs: boolean): Promise<void> {
    if (!targetJobId.trim()) return;
    setHistoryError(null);
    setHistoryLoadingIds((prev) => ({ ...prev, [targetJobId]: true }));
    if (includeLogs) {
      setLogsLoadingJobIds((prev) => ({ ...prev, [targetJobId]: true }));
    }

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
          try {
            const logsRes = await fetch(`${normalizedBaseUrl}/batch/jobs/${targetJobId}/logs`, {
              headers: { 'x-api-key': apiKey },
            });
            if (logsRes.ok) {
              const logsData = decodeApiBody<JobLogsResponse>((await logsRes.json()) as unknown);
              patch.logs = (logsData.logs || []).join('\n');
              patch.info = null;
              patch.error = null;
            } else {
              const t = await logsRes.text();
              if (logsRes.status === 500 && /log stream does not exist/i.test(t)) {
                patch.logs = 'Log stream not ready yet. Try again shortly.';
              } else {
                patch.logs = '';
                patch.error = `Logs failed (${logsRes.status}): ${t}`;
              }
            }
          } catch (err) {
            patch.logs = '';
            patch.error = `Error fetching logs: ${(err as Error).message}`;
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
      if (includeLogs) {
        setLogsLoadingJobIds((prev) => {
          const next = { ...prev };
          delete next[targetJobId];
          return next;
        });
      }
    }
  }

  async function refreshAllHistoryItems(): Promise<void> {
    if (!apiKey) return;
    await fetchHistoryList();
  }

  /* ── notebook param extraction ──────────────────────────── */
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

  const handleFilesChange = useCallback(async (newFiles: File[]): Promise<void> => {
    setFiles(newFiles);
    const nb = newFiles.find((f) => f.name.toLowerCase().endsWith('.ipynb'));
    if (nb) {
      await extractParametersFromNotebook(nb);
    } else {
      setNotebookLoaded(false);
      setFormParams({});
      setExtractInfo(null);
    }
  }, []);

  function updateParam(key: string, value: string) {
    setFormParams((prev) => ({ ...prev, [key]: { ...prev[key], value } }));
  }

  /* ── submit ─────────────────────────────────────────────── */
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const currentFiles = files;

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
            inputMode={entry.type === 'number' ? 'decimal' : undefined}
            lang={entry.type === 'number' ? 'en-US' : undefined}
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
            <ApiConnectionCard
              baseUrl={baseUrl}
              apiKey={apiKey}
              setBaseUrl={setBaseUrl}
              setApiKey={setApiKey}
            />

            <div className="row-grid row-grid-2">
              <SubmitJobCard
                files={files}
                setFiles={setFiles}
                handleFilesChange={handleFilesChange}
                extractInfo={extractInfo}
                notebookLoaded={notebookLoaded}
                hasParams={hasParams}
                formParams={formParams}
                renderParamField={renderParamField}
                executionProfile={executionProfile}
                executionProfiles={EXECUTION_PROFILE_OPTIONS}
                selectedExecutionProfile={selectedExecutionProfile}
                currency={JOB_PROFILE_CURRENCY}
                setExecutionProfile={setExecutionProfile}
                handleSubmit={handleSubmit}
                canSubmit={canSubmit}
                isSubmitting={isSubmitting}
                submitHint={submitHint}
                runError={runError}
                runResult={runResult}
              />

              <JobStatusCard
                handleCheckStatus={handleCheckStatus}
                jobId={jobId}
                setJobId={setJobId}
                runResult={runResult}
                isChecking={isChecking}
                apiKey={apiKey}
                isFetchingLogs={isFetchingLogs}
                handleFetchLogs={handleFetchLogs}
                canFetchLogsNow={canFetchLogsNow}
                isFetchingResults={isFetchingResults}
                handleFetchResults={handleFetchResults}
                canFetchResultsNow={canFetchResultsNow}
                jobError={jobError}
                jobInfo={jobInfo}
                resultsInfo={resultsInfo}
                jobStatus={jobStatus}
                statusUpdatedAt={statusUpdatedAt}
                getStatusClass={getStatusClass}
                jobLogs={jobLogs}
                copyCurrentLogs={async () => {
                  const copied = await copyTextToClipboard(jobLogs.join('\n'));
                  setJobInfo(copied ? 'Logs copied to clipboard.' : 'Failed to copy logs.');
                }}
                resultsError={resultsError}
                resultsDownloadUrl={resultsDownloadUrl}
                jobResults={jobResults}
                downloadResultFile={downloadResultFile}
              />
            </div>
          </>
        ) : (
          <JobHistoryTable
            apiKey={apiKey}
            historyListLoading={historyListLoading}
            historyLoadingIds={historyLoadingIds}
            historyError={historyError}
            jobHistory={jobHistory}
            artifactHydratingJobIds={artifactHydratingJobIds}
            logsLoadingJobIds={logsLoadingJobIds}
            onRefreshList={refreshAllHistoryItems}
            onCopyJobId={copyHistoryJobId}
            onOpenLogs={(jobIdToOpen) => {
              const nextActiveJobId = activeLogsJobId === jobIdToOpen ? null : jobIdToOpen;
              setActiveLogsJobId(nextActiveJobId);
              setActiveParamsJobId(null);
              if (nextActiveJobId) void refreshHistoryItem(jobIdToOpen, true);
            }}
            onOpenParams={(jobIdToOpen) => {
              setActiveLogsJobId(null);
              setActiveParamsJobId(jobIdToOpen);
            }}
            getStatusClass={getStatusClass}
          />
        )}

        <ParamsModal
          item={activeParamsItem}
          onClose={() => setActiveParamsJobId(null)}
        />

        <LogsModal
          item={activeLogsItem}
          isLoading={!!(activeLogsItem && logsLoadingJobIds[activeLogsItem.jobId])}
          onClose={() => setActiveLogsJobId(null)}
          onCopyLogs={async () => {
            if (!activeLogsItem) return;
            const copied = await copyTextToClipboard(activeLogsItem.logs || '');
            patchHistoryItem(activeLogsItem.jobId, {
              info: copied ? 'Logs copied to clipboard.' : null,
              error: copied ? null : 'Failed to copy logs.',
            });
          }}
        />
      </div>
    </div>
  );
};