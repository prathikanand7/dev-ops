import React from 'react';
import { FiAlertCircle, FiCopy, FiDownload, FiFileText, FiInfo, FiPackage, FiRadio, FiSearch } from 'react-icons/fi';
import type { JobResultsResponse, JobStatusResponse, RunResponse } from '../../types';

type JobStatusCardProps = {
  handleCheckStatus: (e: React.FormEvent) => Promise<void>;
  jobId: string;
  setJobId: (value: string) => void;
  runResult: RunResponse | null;
  isChecking: boolean;
  apiKey: string;
  isFetchingLogs: boolean;
  handleFetchLogs: () => Promise<void>;
  canFetchLogsNow: boolean;
  isFetchingResults: boolean;
  handleFetchResults: () => Promise<void>;
  canFetchResultsNow: boolean;
  jobError: string | null;
  jobInfo: string | null;
  resultsInfo: string | null;
  jobStatus: JobStatusResponse | null;
  statusUpdatedAt: Date | null;
  getStatusClass: (status: string) => string;
  jobLogs: string[];
  copyCurrentLogs: () => Promise<void>;
  resultsError: string | null;
  resultsDownloadUrl: string | null;
  jobResults: JobResultsResponse['results'];
  downloadResultFile: (filename: string, b64: string) => void;
};

export const JobStatusCard: React.FC<JobStatusCardProps> = ({
  handleCheckStatus,
  jobId,
  setJobId,
  runResult,
  isChecking,
  apiKey,
  isFetchingLogs,
  handleFetchLogs,
  canFetchLogsNow,
  isFetchingResults,
  handleFetchResults,
  canFetchResultsNow,
  jobError,
  jobInfo,
  resultsInfo,
  jobStatus,
  statusUpdatedAt,
  getStatusClass,
  jobLogs,
  copyCurrentLogs,
  resultsError,
  resultsDownloadUrl,
  jobResults,
  downloadResultFile,
}) => {
  return (
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
              <button type="button" className="btn-neon btn-ghost-neon" onClick={() => void handleFetchLogs()} disabled={isFetchingLogs || !apiKey || !jobId}>
                <FiFileText size={13} />
                {isFetchingLogs ? 'Loading…' : !canFetchLogsNow && !!jobId ? 'Wait for RUNNING' : 'Fetch Logs'}
              </button>
              <button type="button" className="btn-neon btn-ghost-neon" onClick={() => void handleFetchResults()} disabled={isFetchingResults || !apiKey || !jobId}>
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
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.6rem' }}>
                      <p style={{ fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-muted)', marginBottom: 0 }}>Logs</p>
                      <button
                        type="button"
                        className="btn-neon btn-ghost-neon btn-action-compact"
                        onClick={() => void copyCurrentLogs()}
                      >
                        <FiCopy size={12} />Copy Logs
                      </button>
                    </div>
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
  );
};
