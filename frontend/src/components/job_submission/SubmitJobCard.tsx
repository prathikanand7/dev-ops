import React, { useState } from 'react';
import { FiAlertCircle, FiCheckCircle, FiInfo, FiPlay, FiZap } from 'react-icons/fi';
import { DropZone } from '../DropZone';
import type { ExecutionProfileDefinition, FormParams, ParamEntry, RunResponse } from '../../types';

type SubmitJobCardProps = {
  files: File[];
  setFiles: React.Dispatch<React.SetStateAction<File[]>>;
  handleFilesChange: (newFiles: File[]) => Promise<void>;
  extractInfo: string | null;
  notebookLoaded: boolean;
  hasParams: boolean;
  formParams: FormParams;
  renderParamField: (key: string, entry: ParamEntry) => React.ReactNode;
  executionProfile: string;
  executionProfiles: Array<[string, ExecutionProfileDefinition]>;
  selectedExecutionProfile: ExecutionProfileDefinition | null;
  currency: string;
  setExecutionProfile: (value: string) => void;
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
  executionProfiles,
  selectedExecutionProfile,
  currency,
  setExecutionProfile,
  handleSubmit,
  canSubmit,
  isSubmitting,
  submitHint,
  runError,
  runResult,
}) => {
  const [isParamsModalOpen, setIsParamsModalOpen] = useState(false);
  const priceFormatter = new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const memoryGiB = selectedExecutionProfile ? selectedExecutionProfile.memoryMb / 1024 : null;

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
                <div className="param-modal-trigger-row">
                  <p className="form-hint" style={{ margin: 0 }}>
                    {Object.keys(formParams).length} parameter{Object.keys(formParams).length !== 1 ? 's' : ''} extracted and ready to edit.
                  </p>
                  <button
                    type="button"
                    className="btn-neon btn-secondary-neon"
                    onClick={() => setIsParamsModalOpen(true)}
                  >
                    Edit Parameters
                  </button>
                </div>
              )}
            </div>

            {isParamsModalOpen && hasParams && (
              <div className="params-editor-modal-backdrop" role="presentation">
                <div className="params-editor-modal-card" role="dialog" aria-modal="true" aria-label="Edit Parameters">
                  <div className="history-modal-header">
                    <div>
                      <p className="history-modal-eyebrow">Notebook Parameters</p>
                      <h6 className="history-modal-title">Edit Parameters</h6>
                      <p className="history-modal-meta">Adjust values before submitting the job.</p>
                    </div>
                  </div>

                  <div className="params-editor-modal-body">
                    <div className="param-form-grid">
                      {Object.entries(formParams).map(([key, entry]) => renderParamField(key, entry))}
                    </div>
                  </div>

                  <div className="params-editor-modal-actions">
                    <button
                      type="button"
                      className="btn-neon btn-primary-neon"
                      onClick={() => setIsParamsModalOpen(false)}
                    >
                      Save and Close
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="form-group">
              <label className="form-label-styled" htmlFor="execution-profile">Execution Profile</label>
              <select
                id="execution-profile"
                className="form-control-styled"
                value={executionProfile}
                onChange={(e) => setExecutionProfile(e.target.value)}
              >
                {executionProfiles.map(([profileKey, profile]) => (
                  <option key={profileKey} value={profileKey}>
                    {`${profile.displayName} • ${priceFormatter.format(profile.pricingPerHour)}/hour`}
                  </option>
                ))}
              </select>

              {selectedExecutionProfile && (
                <div className="execution-profile-panel">
                  <div className="execution-profile-header">
                    <div>
                      <p className="execution-profile-eyebrow">Estimated Cost</p>
                      <h6 className="execution-profile-title">{selectedExecutionProfile.displayName}</h6>
                      <p className="execution-profile-description">{selectedExecutionProfile.description}</p>
                    </div>
                    <div className="execution-profile-price">
                      {priceFormatter.format(selectedExecutionProfile.pricingPerHour)}
                      <span>/hour</span>
                    </div>
                  </div>

                  <div className="execution-profile-specs">
                    <div className="execution-profile-spec">
                      <span className="execution-profile-spec-label">Backend</span>
                      <strong className="execution-profile-spec-value">{selectedExecutionProfile.backendType}</strong>
                    </div>
                    <div className="execution-profile-spec">
                      <span className="execution-profile-spec-label">vCPU</span>
                      <strong className="execution-profile-spec-value">{selectedExecutionProfile.vcpu}</strong>
                    </div>
                    <div className="execution-profile-spec">
                      <span className="execution-profile-spec-label">Memory</span>
                      <strong className="execution-profile-spec-value">{memoryGiB ? `${memoryGiB} GB` : '-'}</strong>
                    </div>
                    <div className="execution-profile-spec">
                      <span className="execution-profile-spec-label">Storage</span>
                      <strong className="execution-profile-spec-value">{selectedExecutionProfile.storageGb} GB</strong>
                    </div>
                  </div>

                  <p className="execution-profile-disclaimer">
                    <FiInfo size={13} />
                    Indicative hourly estimate only. Final costs vary based on runtime and usage.
                  </p>
                </div>
              )}
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
                <div className="kv-row"><span className="kv-label">Profile</span><span className="kv-value">{selectedExecutionProfile ? `${selectedExecutionProfile.displayName} (${runResult.execution_profile || executionProfile})` : (runResult.execution_profile || executionProfile)}</span></div>
                {selectedExecutionProfile && (
                  <div className="kv-row"><span className="kv-label">Est. Cost</span><span className="kv-value">{`${priceFormatter.format(selectedExecutionProfile.pricingPerHour)}/hour`}</span></div>
                )}
                {runResult.message && <div className="kv-row"><span className="kv-label">Message</span><span className="kv-value">{runResult.message}</span></div>}
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};
