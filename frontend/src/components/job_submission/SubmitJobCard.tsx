import React from 'react';
import { FiAlertCircle, FiCheckCircle, FiInfo, FiPlay, FiZap } from 'react-icons/fi';
import { DropZone } from '../DropZone';
import type { FormParams, ParamEntry, RunResponse } from '../../types';

type SubmitJobCardProps = {
  files: File[];
  setFiles: React.Dispatch<React.SetStateAction<File[]>>;
  handleFilesChange: (newFiles: File[]) => Promise<void>;
  extractInfo: string | null;
  notebookLoaded: boolean;
  hasParams: boolean;
  formParams: FormParams;
  renderParamField: (key: string, entry: ParamEntry) => React.ReactNode;
  executionProfile: 'standard' | 'ec2_200gb';
  setExecutionProfile: (value: 'standard' | 'ec2_200gb') => void;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  canSubmit: boolean;
  isSubmitting: boolean;
  submitHint: string | null;
  runError: string | null;
  runResult: RunResponse | null;
};

export const SubmitJobCard: React.FC<SubmitJobCardProps> = ({
  files,
  setFiles,
  handleFilesChange,
  extractInfo,
  notebookLoaded,
  hasParams,
  formParams,
  renderParamField,
  executionProfile,
  setExecutionProfile,
  handleSubmit,
  canSubmit,
  isSubmitting,
  submitHint,
  runError,
  runResult,
}) => {
  return (
    <div className="glass-card">
      <div className="card-inner">
        <div className="card-head">
          <div className="card-head-icon"><FiZap size={14} /></div>
          <h5>Trigger Notebook Run</h5>
        </div>
        <div className="card-body-inner">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <DropZone
                label="Upload Files"
                files={files}
                setFiles={setFiles}
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

            <div className="form-group">
              <label className="form-label-styled">Parameters</label>

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
                <div className="param-form-grid">
                  {Object.entries(formParams).map(([key, entry]) => renderParamField(key, entry))}
                </div>
              )}
            </div>

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
              <p className="form-hint">
                <FiInfo size={15} style={{ marginRight: 4, verticalAlign: 'middle' }} />
                Use <code>ec2_200gb</code> for high-storage workloads.
              </p>
            </div>

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
  );
};
