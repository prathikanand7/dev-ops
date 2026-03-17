import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const frontendRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(frontendRoot, '..');
const sourcePath = path.join(repoRoot, 'job_profiles.json');
const outputDir = path.join(frontendRoot, 'src', 'config');
const outputPath = path.join(outputDir, 'jobProfiles.generated.ts');

function toExecutionProfileDefinition(profile) {
  return {
    displayName: profile.display_name,
    description: profile.description,
    backendType: profile.backend_type,
    vcpu: profile.vcpu,
    maxVcpus: profile.max_vcpus,
    memoryMb: profile.memory_mb,
    storageGb: profile.storage_gb,
    pricingPerHour: profile.pricing_per_hour,
    isDefault: profile.is_default,
  };
}

async function main() {
  const raw = await readFile(sourcePath, 'utf8');
  const parsed = JSON.parse(raw);

  const currency = parsed?.global_settings?.currency || 'USD';
  const profiles = parsed?.profiles || {};

  const transformedProfiles = Object.fromEntries(
    Object.entries(profiles).map(([profileKey, profileValue]) => [
      profileKey,
      toExecutionProfileDefinition(profileValue),
    ]),
  );

  const fileContents = `import type { ExecutionProfileDefinition } from '../types';

// This file is generated from ../job_profiles.json by scripts/generate-job-profiles.mjs.
// Do not edit it by hand.
export const JOB_PROFILE_CURRENCY = ${JSON.stringify(currency)};

export const EXECUTION_PROFILES: Record<string, ExecutionProfileDefinition> = ${JSON.stringify(transformedProfiles, null, 2)};
`;

  await mkdir(outputDir, { recursive: true });
  await writeFile(outputPath, `${fileContents.trim()}\n`, 'utf8');
  process.stdout.write(`Generated ${path.relative(frontendRoot, outputPath)} from ${path.relative(repoRoot, sourcePath)}\n`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
