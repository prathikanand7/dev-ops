import type { ExecutionProfileDefinition } from '../types';
import { EXECUTION_PROFILES, JOB_PROFILE_CURRENCY } from './jobProfiles.generated';

export { JOB_PROFILE_CURRENCY };

export const EXECUTION_PROFILE_OPTIONS = Object.entries(EXECUTION_PROFILES);

export const DEFAULT_EXECUTION_PROFILE =
  EXECUTION_PROFILE_OPTIONS.find(([, profile]) => profile.isDefault)?.[0]
  ?? EXECUTION_PROFILE_OPTIONS[0]?.[0]
  ?? 'standard';

export function isKnownExecutionProfile(profileKey: string): boolean {
  return profileKey in EXECUTION_PROFILES;
}

export function getExecutionProfile(profileKey: string): ExecutionProfileDefinition | null {
  return EXECUTION_PROFILES[profileKey] || null;
}
