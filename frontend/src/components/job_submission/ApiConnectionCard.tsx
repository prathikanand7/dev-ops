import React from 'react';
import { FiLink } from 'react-icons/fi';

type ApiConnectionCardProps = {
  baseUrl: string;
  apiKey: string;
  setBaseUrl: (value: string) => void;
  setApiKey: (value: string) => void;
};

export const ApiConnectionCard: React.FC<ApiConnectionCardProps> = ({
  baseUrl,
  apiKey,
  setBaseUrl,
  setApiKey,
}) => {
  return (
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
  );
};
