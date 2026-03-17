import React from 'react';
import { FiCopy } from 'react-icons/fi';
import type { JobHistoryItem } from '../../types';

type LogsModalProps = {
  item: JobHistoryItem | null;
  isLoading: boolean;
  onClose: () => void;
  onCopyLogs: () => void | Promise<void>;
};

export const LogsModal: React.FC<LogsModalProps> = ({ item, isLoading, onClose, onCopyLogs }) => {
  if (!item) return null;

  return (
    <div className="history-modal-backdrop" onClick={onClose} role="presentation">
      <div
        className="history-modal-card history-modal-card-logs"
        role="dialog"
        aria-modal="true"
        aria-labelledby="history-logs-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="history-modal-header">
          <div>
            <p className="history-modal-eyebrow">Run Logs</p>
            <h6 id="history-logs-title" className="history-modal-title">{item.notebookName || 'Notebook Run'}</h6>
            <p className="history-modal-meta">{item.jobId}</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            {!isLoading && item.logs && (
              <button
                type="button"
                className="btn-neon btn-ghost-neon btn-action-compact"
                onClick={() => void onCopyLogs()}
              >
                <FiCopy size={12} />Copy Logs
              </button>
            )}
            <button
              type="button"
              className="btn-neon btn-ghost-neon btn-action-compact"
              onClick={onClose}
            >
              Close
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="logs-terminal history-logs-terminal history-logs-modal-terminal" style={{ color: 'var(--ink-muted)', fontStyle: 'italic' }}>
            Fetching logs from the cluster...
          </div>
        ) : (
          <pre className="logs-terminal history-logs-terminal history-logs-modal-terminal">{item.logs || 'No logs available.'}</pre>
        )}

        {(item.info || item.error) && !isLoading && (
          <div className={`alert-neon ${item.error ? 'alert-danger-neon' : 'alert-info-neon'}`} style={{ marginTop: '0.7rem' }}>
            {item.error || item.info}
          </div>
        )}
      </div>
    </div>
  );
};
