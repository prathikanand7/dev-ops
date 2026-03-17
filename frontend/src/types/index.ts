/* ─── API response types ─────────────────────────────────────── */
export type RunResponse        = { message: string; job_id: string; execution_profile?: string; };
export type JobStatusResponse  = { job_id: string; job_name?: string; status: string; createdAt?: number; startedAt?: number; stoppedAt?: number; error?: string; };
export type JobLogsResponse    = { job_id: string; logs: string[]; };
export type JobResultsResponse = { job_id: string; status?: string; download_url?: string; results: Array<{ filename: string; content_base64: string; }>; };

/* ─── UI types ───────────────────────────────────────────────── */
export type ThemeMode = 'dark' | 'light';
export type AppPage   = 'submission' | 'history';

/* ─── Param form types ───────────────────────────────────────── */
export type ParamType  = 'number' | 'boolean' | 'string';
export type ParamEntry = { value: string; type: ParamType; };
export type FormParams = Record<string, ParamEntry>;

export type SubmissionDraft = {
  formParams: FormParams;
  notebookLoaded: boolean;
  extractInfo: string | null;
  executionProfile: 'standard' | 'ec2_200gb';
};

/* ─── Job history types ──────────────────────────────────────── */
export type JobHistoryItem = {
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

export type JobHistoryListResponse = {
  jobs: JobHistoryItem[];
};
