# LifeWatch Notebook Platform DevOps

Infrastructure, CI/CD, and validation assets for running notebooks through AWS Batch behind an API Gateway and Lambda control plane.
<!-- Maintainer note: keep this README aligned with active workflow filenames in .github/workflows. -->

## Scope

- Terraform infrastructure for the `dev` environment.
- Lambda handlers and API request client scripts.
- Worker container build and publish pipeline.
- End-to-end notebook validation on AWS.
- Frontend operator UI for job submission and history.
- Demo notebook fixtures, including lightweight examples.

## Critical Operating Policy

The `dev` environment is shared by teammates.

- Notebook E2E workflows must not run `terraform destroy`.
- Cleanup is limited to transient AWS Batch EC2 instances created during execution.
- Terraform-managed infrastructure is intentionally preserved after E2E runs.

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
| Smoke Test Worker Containerization | `.github/workflows/smoke-test-worker-containerization.yml` | Builds worker image and validates container startup. |
| Deploy Worker Image to ECR | `.github/workflows/deploy-worker-ecr.yml` | Publishes worker image tags to ECR. |
| Terraform CI | `.github/workflows/test-terraform-plan.yml` | Runs `fmt`, `validate`, `plan`, and optional `terraform test`. |
| Notebook E2E Deploy and Run | `.github/workflows/e2e-notebook-deploy-and-run.yml` | Applies infra, runs notebook E2E matrix, uploads artefacts, then performs EC2-only cleanup. |

## Documentation Index

- [Notebook E2E Runbook](docs/e2e-notebook-testing.md)
- [Lightweight Notebook Fixtures](demo_input/lightweight-notebooks/README.md)
- [Terraform `dev` Environment](lifewatch_batch_platform/terraform/environments/dev/readme.md)
- [Frontend Guide](frontend/README.md)
- [Terraform Bootstrap Guide](terraform-bootstrap/readme.md)

## Quick Start (Frontend)

```bash
cd frontend
npm install
npm run dev
```

## Terraform Environment Notes

For detailed infrastructure inputs, outputs, and module dependencies, use:

`lifewatch_batch_platform/terraform/environments/dev/readme.md`

## Security and Secrets

- Never commit API keys, AWS keys, or Terraform state.
- Required credentials must be injected via GitHub Actions secrets.
- E2E API authentication is validated through both positive and negative tests.
<!-- Policy reminder: do not document full stack teardown for shared environments. -->
