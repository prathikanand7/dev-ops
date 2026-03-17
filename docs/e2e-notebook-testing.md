# Notebook E2E Testing Runbook

This runbook defines how notebook end-to-end validation is executed in AWS and what cleanup scope is allowed in the shared `dev` environment.
<!-- Maintainer note: this runbook must mirror .github/workflows/e2e-notebook-deploy-and-run.yml. -->

## Workflow

- Workflow file: `.github/workflows/e2e-notebook-deploy-and-run.yml`
- Workflow name: `Notebook E2E Deploy and Run`
- Triggers:
  - `workflow_dispatch` (manual)
  - `workflow_run` after `Deploy Worker Image to ECR` completes successfully on `main`

## Preconditions

The following GitHub repository secrets must be configured:

- `AWS_ACCESS_KEY`
- `AWS_SECRET_KEY`
- `CONTAINER_IMAGE`
- `BATCH_EXECUTION_ROLE_ARN`
- `TERRAFORM_ENV_DIR` (for example: `./lifewatch_batch_platform/terraform/environments/dev`)

## Test Matrix

The workflow executes:

1. Notebook E2E on `ec2_200gb`
2. Notebook E2E on `standard`
3. Negative authentication check with an invalid API key (expects `401` or `403`)

Each run uploads artefacts under:

- `${TERRAFORM_ENV_DIR}/e2e_outputs/ec2_200gb`
- `${TERRAFORM_ENV_DIR}/e2e_outputs/standard`
- `${TERRAFORM_ENV_DIR}/e2e_outputs/negative`

## Cleanup Policy (Critical)

The `dev` Terraform stack is shared and must stay available.

- Allowed automatic cleanup:
  - terminate lingering EC2 instances tagged with name prefix `lifewatch-batch-ec2-*`
- Not allowed in E2E workflow:
  - `terraform destroy`
  - removal of API Gateway, Lambda, API keys, usage plans, VPC resources, queues, or shared S3 resources

## Operational Sequence

1. Checkout target commit.
2. Configure AWS credentials.
3. Run `terraform init` and `terraform apply` in `TERRAFORM_ENV_DIR`.
4. Read `api_gateway_url` and `api_key` Terraform outputs.
5. Execute notebook E2E scenarios.
6. Upload artefacts.
7. Terminate any lingering Batch EC2 instances and verify zero remain.

## Failure Handling

- If notebook execution fails:
  - artefacts are still uploaded (`if: always()`).
  - EC2 cleanup still runs (`if: always()`).
- If EC2 cleanup fails:
  - workflow fails and prints instance inventory table for investigation.

## Manual Verification Commands

Use these after an E2E run if manual confirmation is required:

```bash
# List lingering Batch EC2 instances
aws ec2 describe-instances \
  --region eu-west-1 \
  --filters "Name=tag:Name,Values=lifewatch-batch-ec2-*" \
            "Name=instance-state-name,Values=pending,running,stopping,stopped,shutting-down" \
  --query "Reservations[].Instances[].{Id:InstanceId,State:State.Name,Name:Tags[?Key=='Name']|[0].Value}" \
  --output table
```

## Change Management Rule

Any proposal to reintroduce full infrastructure teardown must be reviewed with the team first, and must not run automatically in shared branches.
