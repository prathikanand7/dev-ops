import React from 'react';
import { FiDownload, FiFileText, FiInfo, FiPackage, FiRefreshCw, FiClock } from 'react-icons/fi';
import type { JobHistoryItem } from '../../types';

type JobHistoryTableProps = {
  apiKey: string;
  historyListLoading: boolean;
  historyLoadingIds: Record<string, boolean>;
  historyError: string | null;
  jobHistory: JobHistoryItem[];
  artifactHydratingJobIds: Record<string, boolean>;
  logsLoadingJobIds: Record<string, boolean>;
  onRefreshList: () => Promise<void>;
  onCopyJobId: (jobId: string) => Promise<void>;
  onOpenLogs: (jobId: string) => void;
  onOpenParams: (jobId: string) => void;
  getStatusClass: (status: string) => string;
};

export const JobHistoryTable: React.FC<JobHistoryTableProps> = ({
  apiKey,
  historyListLoading,
  historyLoadingIds,
  historyError,
  jobHistory,
  artifactHydratingJobIds,
  logsLoadingJobIds,
  onRefreshList,
  onCopyJobId,
  onOpenLogs,
  onOpenParams,
  getStatusClass,
}) => {
  return (
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
                Condensed runs list from cloud history. Use action buttons to inspect logs or parameters.
              </p>
              <button
                type="button"
                className="btn-neon btn-ghost-neon"
                onClick={() => void onRefreshList()}
                disabled={!apiKey || historyListLoading || Object.keys(historyLoadingIds).length > 0}
              >
                <FiRefreshCw size={13} />{historyListLoading ? 'Refreshing…' : 'Refresh List'}
              </button>
            </div>

            {historyError && (
              <div className="alert-neon alert-warning-neon" style={{ marginTop: '0.9rem' }}>{historyError}</div>
            )}

            {!apiKey ? (
              <div className="param-pending" style={{ marginTop: '0.95rem' }}>
                <FiInfo size={14} />
                <span>Enter API key in Job Submission tab to load cloud history.</span>
              </div>
            ) : jobHistory.length === 0 ? (
              <div className="param-pending" style={{ marginTop: '0.95rem' }}>
                <FiInfo size={14} />
                <span>No jobs found in cloud history.</span>
              </div>
            ) : (
              <>
                <div className="history-scroll-list">
                  <div className="history-table history-table-head">
                    <span>Job ID</span>
                    <span>Notebook</span>
                    <span>Status</span>
                    <span>Created</span>
                    <span>Actions</span>
                  </div>

                  {jobHistory.map((item) => {
                    const createdText = item.submittedAt ? new Date(item.submittedAt).toLocaleString() : '-';
                    const isArtifactHydrating = !!artifactHydratingJobIds[item.jobId];

                    return (
                      <div key={item.jobId} className="history-row-wrapper">
                        <div className="history-table history-table-row">
                          <button
                            type="button"
                            data-label="Job ID"
                            className="history-cell-jobid history-jobid-button"
                            title={`Copy ${item.jobId}`}
                            onClick={() => void onCopyJobId(item.jobId)}
                          >
                            {item.jobId}
                          </button>
                          <span data-label="Notebook" className="history-cell-notebook" title={item.notebookName}>{item.notebookName || '-'}</span>
                          <span data-label="Status"><span className={`status-pill ${getStatusClass(item.status)}`}>{item.status}</span></span>
                          <span data-label="Created" className="history-cell-created" title={createdText}>{createdText}</span>
                          <span data-label="Actions" className="history-actions-cell">
                            <button
                              type="button"
                              className="btn-neon btn-secondary-neon btn-action-compact"
                              onClick={() => onOpenLogs(item.jobId)}
                              disabled={!apiKey || logsLoadingJobIds[item.jobId]}
                            >
                              <FiFileText size={12} />{logsLoadingJobIds[item.jobId] ? 'Loading' : 'Logs'}
                            </button>
                            <button
                              type="button"
                              className="btn-neon btn-secondary-neon btn-action-compact"
                              onClick={() => onOpenParams(item.jobId)}
                            >
                              <FiPackage size={12} />Params
                            </button>
                            {item.artifactUrl && (
                              <a
                                href={item.artifactUrl}
                                target="_blank"
                                rel="noreferrer"
                                className="btn-neon btn-success-neon btn-action-compact"
                                style={{ textDecoration: 'none', display: 'inline-flex' }}
                              >
                                <FiDownload size={12} />Artifacts
                              </a>
                            )}
                            {!item.artifactUrl && item.status === 'SUCCEEDED' && isArtifactHydrating && (
                              <button
                                type="button"
                                className="btn-neon btn-success-neon btn-action-compact"
                                disabled
                              >
                                <span className="btn-loading-dot" aria-hidden="true" />Artifacts
                              </button>
                            )}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
