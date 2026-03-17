import React from 'react';
import type { JobHistoryItem } from '../../types';

type ParamsModalProps = {
  item: JobHistoryItem | null;
  onClose: () => void;
};

export const ParamsModal: React.FC<ParamsModalProps> = ({ item, onClose }) => {
  if (!item) return null;

  return (
    <div className="history-modal-backdrop" onClick={onClose} role="presentation">
      <div
        className="history-modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="history-params-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="history-modal-header">
          <div>
            <p className="history-modal-eyebrow">Run Parameters</p>
            <h6 id="history-params-title" className="history-modal-title">{item.notebookName || 'Notebook Run'}</h6>
            <p className="history-modal-meta">{item.jobId}</p>
          </div>
          <button
            type="button"
            className="btn-neon btn-ghost-neon btn-action-compact"
            onClick={onClose}
          >
            Close
          </button>
        </div>

        {Object.keys(item.params || {}).length === 0 ? (
          <p className="form-hint" style={{ marginTop: 0 }}>No parameters captured for this run.</p>
        ) : (
          <div className="history-params-table-shell history-params-modal-table-popup">
            <table className="history-params-table-header">
              <colgroup>
                <col style={{ width: '42%' }} />
                <col style={{ width: '58%' }} />
              </colgroup>
              <thead>
                <tr>
                  <th>Parameter Name</th>
                  <th>Value</th>
                </tr>
              </thead>
            </table>

            <div className="history-params-modal-table history-params-table-body-scroll">
              <table>
                <colgroup>
                  <col style={{ width: '42%' }} />
                  <col style={{ width: '58%' }} />
                </colgroup>
                <tbody>
                  {Object.entries(item.params).map(([paramKey, paramValue]) => (
                    <tr key={paramKey}>
                      <td className="param-name-cell">{paramKey}</td>
                      <td className="param-value-cell">{String(paramValue)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
