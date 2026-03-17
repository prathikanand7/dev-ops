import type { JobHistoryItem, ParamType, SubmissionDraft } from '../types';
import { DEFAULT_EXECUTION_PROFILE, isKnownExecutionProfile } from '../config/jobProfiles';

export const SUBMISSION_DRAFT_KEY = 'nop-submission-draft';

export function detectType(v: string | number | boolean): ParamType {
  if (typeof v === 'number') return 'number';
  if (typeof v === 'boolean') return 'boolean';
  return 'string';
}

export function isEnvironmentFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return name.endsWith('.yaml') || name.endsWith('.yml') || name.endsWith('.txt');
}

export function normalizeHistoryItem(raw: Partial<JobHistoryItem> & Record<string, unknown>): JobHistoryItem {
  const paramsRaw = raw.params;
  const params: Record<string, string> = {};
  if (paramsRaw && typeof paramsRaw === 'object' && !Array.isArray(paramsRaw)) {
    Object.entries(paramsRaw as Record<string, unknown>).forEach(([k, v]) => {
      params[k] = String(v ?? '');
    });
  }

  return {
    jobId: String(raw.jobId || ''),
    submittedAt: String(raw.submittedAt || ''),
    notebookName: String(raw.notebookName || 'Unknown'),
    environmentName: String(raw.environmentName || 'Unknown'),
    executionProfile: String(raw.executionProfile || 'unknown'),
    params,
    status: String(raw.status || 'UNKNOWN'),
    logs: String(raw.logs || ''),
    artifactUrl: typeof raw.artifactUrl === 'string' ? raw.artifactUrl : null,
    s3Uri: typeof raw.s3Uri === 'string' ? raw.s3Uri : null,
    info: typeof raw.info === 'string' ? raw.info : null,
    error: typeof raw.error === 'string' ? raw.error : null,
    lastCheckedAt: typeof raw.lastCheckedAt === 'string' ? raw.lastCheckedAt : null,
  };
}

export function safeLoadSubmissionDraft(): SubmissionDraft {
  try {
    const raw = window.localStorage.getItem(SUBMISSION_DRAFT_KEY);
    if (!raw) {
      return { formParams: {}, notebookLoaded: false, extractInfo: null, executionProfile: DEFAULT_EXECUTION_PROFILE };
    }
    const parsed = JSON.parse(raw) as Partial<SubmissionDraft>;
    const executionProfile = typeof parsed.executionProfile === 'string' && isKnownExecutionProfile(parsed.executionProfile)
      ? parsed.executionProfile
      : DEFAULT_EXECUTION_PROFILE;
    return {
      formParams: parsed.formParams && typeof parsed.formParams === 'object' ? parsed.formParams : {},
      notebookLoaded: !!parsed.notebookLoaded,
      extractInfo: typeof parsed.extractInfo === 'string' ? parsed.extractInfo : null,
      executionProfile,
    };
  } catch {
    return { formParams: {}, notebookLoaded: false, extractInfo: null, executionProfile: DEFAULT_EXECUTION_PROFILE };
  }
}
