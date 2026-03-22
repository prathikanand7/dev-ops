# LifeWatch Notebook Platform DevOps

Infrastructure, CI/CD, and validation assets for running notebooks through AWS Batch behind an API Gateway and Lambda control plane.

## Components

- Terraform infrastructure for the dev environment.
- Lambda handlers and API request client scripts.
- Worker container build and publish pipeline.
- End-to-end notebook validation on AWS.
- Frontend operator UI for job submission and history.
- Demo notebook fixtures, including lightweight examples.

## Setup Decisions

The dev environment is shared by teammates.

- Notebook E2E workflows must not run terraform destroy.
- Cleanup is limited to transient AWS Batch EC2 instances created during execution.
- Terraform-managed infrastructure is intentionally preserved after E2E runs.

## Prerequisites

- Terraform 1.6 or newer.
- AWS CLI configured with credentials that can manage the target dev stack.
- Docker (for worker image build and local checks).
- Node.js 18+ and npm (for frontend local runs).
- Python 3.10+ (for helper scripts and selected workflows).

## Repository Layout

```text
dev-ops/
├── .github/workflows/                           # CI/CD and E2E workflows
├── lifewatch_batch_platform/terraform/          # Terraform env + reusable modules + client scripts
├── frontend/                                    # React + TypeScript operator UI
├── worker/                                      # Batch worker image definition
├── demo_input/                                  # Notebook and payload fixtures for tests/manual runs
├── terraform-bootstrap/                         # Remote-state bootstrap resources
└── job_profiles.json                            # Shared execution-profile catalogue
```

## Core Workflows

| Workflow | File | Purpose |
|---|---|---|
| Smoke Test Worker Containerization | .github/workflows/smoke-test-worker-containerization.yml | Builds worker image and validates container startup. |
| Deploy Worker Image to ECR | .github/workflows/deploy-worker-ecr.yml | Publishes worker image tags to ECR. |
| Terraform CI | .github/workflows/test-terraform-plan.yml | Runs fmt, validate, plan, and optional terraform test. |
| Notebook E2E Deploy and Run | .github/workflows/e2e-notebook-deploy-and-run.yml | Applies infra, runs notebook E2E matrix, uploads artifacts, then performs EC2-only cleanup. |

## Documentation Index

- [Notebook E2E Runbook](.github/workflows/e2e-notebook-testing.md)
- [Lightweight Notebook Fixtures](demo_input/lightweight-notebooks/README.md)
- [Terraform dev Environment](lifewatch_batch_platform/terraform/environments/dev/readme.md)
- [Frontend Guide](frontend/README.md)
- [Terraform Bootstrap Guide](terraform-bootstrap/readme.md)

## Quick Start

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Terraform Dev Environment

```bash
cd lifewatch_batch_platform/terraform/environments/dev
terraform init
terraform plan
```

## Deployment Order (Recommended)

1. Initialize remote state bootstrap resources from terraform-bootstrap if not already provisioned.
2. Apply the dev environment Terraform stack.
3. Build and publish worker image to ECR.
4. Run notebook E2E workflows.

## Onboarding Checklist

Use this checklist for new contributors working on the dev environment.

1. Clone the repository and verify toolchain versions from Prerequisites.
2. Confirm AWS access by running aws sts get-caller-identity.
3. Ensure access to required GitHub repository secrets (see matrix below).
4. Run Terraform init and plan from lifewatch_batch_platform/terraform/environments/dev.
5. Run worker smoke test locally with docker build ./worker and a quick container run.
6. Start frontend locally (npm run dev) and verify API base URL configuration.
7. Review the E2E runbook before triggering shared-environment workflows.

## Local Validation Commands

```bash
# Terraform style and validation
terraform fmt -recursive
terraform -chdir=lifewatch_batch_platform/terraform/environments/dev validate

# Module tests (if present)
terraform -chdir=lifewatch_batch_platform/terraform/modules/api_gateway test

# Frontend checks
cd frontend && npm run build
```

## Terraform Environment Notes

For detailed infrastructure inputs, outputs, and module dependencies, use:

lifewatch_batch_platform/terraform/environments/dev/readme.md

## Security and Secrets

- Never commit API keys, AWS keys, or Terraform state.
- Required credentials must be injected via GitHub Actions secrets or secured local environment configuration.
- E2E API authentication is validated through both positive and negative tests.
- For local Terraform runs, var files may be used, for example terraform apply -var-file secrets.tfvars.
- Preferred CI pattern is environment variables and secret stores instead of long-lived local secret files.

## GitHub Secrets by Workflow

The following repository secrets are required by CI/CD workflows.

| Workflow | Required secrets |
|---|---|
| Smoke Test Worker Containerization | None |
| Deploy Worker Image to ECR | AWS_ACCESS_KEY, AWS_SECRET_KEY |
| Terraform CI | TERRAFORM_ENV_DIR, AWS_ACCESS_KEY, AWS_SECRET_KEY, CONTAINER_IMAGE, BATCH_EXECUTION_ROLE_ARN |
| Notebook E2E Deploy and Run | TERRAFORM_ENV_DIR, AWS_ACCESS_KEY, AWS_SECRET_KEY, CONTAINER_IMAGE, BATCH_EXECUTION_ROLE_ARN |

Notes:
- TERRAFORM_ENV_DIR should point to the active environment directory, for example lifewatch_batch_platform/terraform/environments/dev.
- Rotate AWS credentials regularly and prefer short-lived credentials where possible.

## Troubleshooting

### Terraform CI fails at plan

- Confirm TERRAFORM_ENV_DIR points to a valid environment folder.
- Verify CONTAINER_IMAGE and BATCH_EXECUTION_ROLE_ARN are set in repository secrets.
- Re-run terraform init locally in the same environment directory to reproduce.

### terraform test fails after module refactor

- Check whether tests still reference removed resources after architecture changes.
- Update assertions to match source of truth (for example OpenAPI body imports versus explicit method resources).
- Run module tests locally before pushing.

### E2E fails with API auth errors

- Validate API key output from Terraform and ensure request header uses x-api-key.
- Run the negative API key check expectations: 401 or 403 should be treated as pass for invalid keys.
- Confirm gateway-level CORS responses are present for API Gateway-generated errors.

### E2E completes but leaves compute instances

- Verify EC2 cleanup step logs in the E2E workflow artifacts.
- Check for instances tagged with lifewatch-batch-ec2-* and terminate manually if needed.
- Keep terraform destroy disabled for shared dev environment policy compliance.

### Worker image deploy does not trigger downstream E2E

- Confirm Deploy Worker Image to ECR ran on main and completed successfully.
- Check workflow_run trigger conditions and branch filters in dependent workflows.
- Use manual workflow_dispatch as a controlled fallback.

## Notes on Scope

- This repository is focused on infrastructure and delivery workflows.
- Application-level backend behavior and frontend runtime details are documented in their respective subproject guides.
