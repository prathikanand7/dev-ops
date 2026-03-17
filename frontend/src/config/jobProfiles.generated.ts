import type { ExecutionProfileDefinition } from '../types';

// This file is generated from ../job_profiles.json by scripts/generate-job-profiles.mjs.
// Do not edit it by hand.
export const JOB_PROFILE_CURRENCY = "USD";

export const EXECUTION_PROFILES: Record<string, ExecutionProfileDefinition> = {
  "standard": {
    "displayName": "Standard Compute (Fargate)",
    "description": "Serverless Fargate compute for general tasks.",
    "backendType": "FARGATE",
    "vcpu": 1,
    "maxVcpus": 256,
    "memoryMb": 8192,
    "storageGb": 21,
    "pricingPerHour": 0.05,
    "isDefault": true
  },
  "ec2_200gb": {
    "displayName": "High Storage Compute (EC2)",
    "description": "Dedicated EC2 instance with 200GB attached EBS volume.",
    "backendType": "EC2",
    "vcpu": 2,
    "maxVcpus": 256,
    "memoryMb": 16384,
    "storageGb": 200,
    "pricingPerHour": 0.15,
    "isDefault": false
  }
};
