# Environment: dev

Deploys the full Lifewatch high-compute stack to the `dev` stage in `eu-west-1`. All infrastructure is assembled from reusable modules in `../../modules/`.

## Architecture overview

```
API Gateway (REST)
    │
    ├── POST /batch/jobs              → lambda_batch_trigger  ──► AWS Batch
    ├── GET  /batch/jobs/{id}         → lambda_job_status     ──► AWS Batch
    ├── GET  /batch/jobs/{id}/logs    → lambda_job_logs       ──► CloudWatch
    ├── GET  /batch/jobs/{id}/results → lambda_job_results    ──► S3
    └── GET  /batch/jobs/history_list → lambda_job_history_list
                                                                    ▲
                                                             Batch workers
                                                          (Fargate or EC2)
```

Requests are authenticated with an API key enforced via a usage plan (burst: 5, rate: 10 req/s). An optional request quota can be enabled via `quota_limit` in `terraform.tfvars`.

Batch jobs run inside a private VPC. Traffic to AWS services (ECR, S3, CloudWatch, ECS) flows through VPC endpoints rather than the public internet.

---

## Prerequisites

Before running `terraform apply`, ensure the following exist outside this stack:

| Resource | Description |
|---|---|
| S3 bucket `lifewatch-terraform-state-eu-west-1` | Remote state bucket |
| DynamoDB table `lifewatch-terraform-locks` | State locking table |
| IAM role `BatchEcsTaskExecutionRole` | ECS task execution role for Fargate (pulls ECR images, ships logs) |
| ECR repository `r-notebook-worker` | Container image repository |
| Lambda ZIP files | See [Lambda deployments](#lambda-deployments) below |

---

## Usage

```bash
# First time only
terraform init

# Preview changes
terraform plan

# Deploy
terraform apply

# Retrieve the API key after deploy
terraform output -raw api_key
```

---

## Lambda deployments

Each Lambda function expects a ZIP file to exist at the path configured in `terraform.tfvars` before `terraform plan` runs, because `filebase64sha256()` is evaluated at plan time.

| Variable | Default path | Handler |
|---|---|---|
| `lambda_trigger_filename` | `../../backend_lambda_artifacts/lambda.zip` | `lambda_function.lambda_handler` |
| `lambda_status_filename` | `../../backend_lambda_artifacts/status_lambda.zip` | `status.lambda_handler` |
| `lambda_logs_filename` | `../../backend_lambda_artifacts/logs_lambda.zip` | `logs.lambda_handler` |
| `lambda_results_filename` | `../../backend_lambda_artifacts/results_lambda.zip` | `results.lambda_handler` |
| `lambda_history_list_filename` | `../../backend_lambda_artifacts/history_list_lambda.zip` | `history_list.lambda_handler` |

Paths are relative to the `environments/dev/` directory. If your ZIPs live elsewhere, update the paths in `terraform.tfvars` accordingly (e.g. `"../../lambdas/lambda.zip"`).

---

## Module dependency graph

```
vpc
 ├── security_groups
 └── vpc_endpoints
      │
      ├── s3_batch_payloads
      │    ├── lambda_iam
      │    │    ├── lambda_batch_trigger
      │    │    ├── lambda_job_status
      │    │    ├── lambda_job_logs
      │    │    ├── lambda_job_results
      │    │    └── lambda_job_history_list
      │    ├── batch_job_definition_fargate
      │    └── batch_job_definition_ec2
      │
      ├── batch_compute_fargate
      │    └── batch_queue_fargate
      │
      └── batch_compute_ec2
           └── batch_queue_ec2

lambda_batch_trigger ──► batch_queue_fargate
                     ──► batch_job_definition_fargate
                     ──► batch_queue_ec2
                     ──► batch_job_definition_ec2

api_gateway ──► lambda_batch_trigger
            ──► lambda_job_status
            ──► lambda_job_logs
            ──► lambda_job_results
            ──► lambda_job_history_list

api_key_usage_plan ──► api_gateway
```

---

## Modules used

| Module | Source | Description |
|---|---|---|
| `vpc` | `modules/vpc` | VPC, public/private subnets, IGW, NAT gateway, route tables |
| `security_groups` | `modules/security_groups` | Batch and VPC endpoint security groups |
| `vpc_endpoints` | `modules/vpc_endpoints` | Interface and gateway endpoints for S3, ECR, ECS, CloudWatch |
| `s3_batch_payloads` | `modules/s3_batch_payloads` | S3 bucket for job input/output files |
| `batch_compute_fargate` | `modules/batch_fargate/batch_compute_fargate` | Managed Fargate compute environment |
| `batch_job_definition_fargate` | `modules/batch_fargate/batch_job_definition_fargate` | Fargate job definition (1 vCPU / 8 GB) |
| `batch_queue_fargate` | `modules/batch_fargate/batch_queue_fargate` | Fargate job queue (priority 10) |
| `batch_compute_ec2` | `modules/batch_ec2/batch_compute_ec2` | Managed EC2 compute environment with 200 GB gp3 volumes |
| `batch_job_definition_ec2` | `modules/batch_ec2/batch_job_definition_ec2` | EC2 job definition (2 vCPU / 16 GB) |
| `batch_queue_ec2` | `modules/batch_ec2/batch_queue_ec2` | EC2 job queue (priority 20) |
| `lambda_iam` | `modules/lambda_iam` | Shared IAM role for all Lambda functions |
| `lambda_batch_trigger` | `modules/lambda/lambda_batch_trigger` | Handles POST /batch/jobs |
| `lambda_job_status` | `modules/lambda/lambda_job_status` | Handles GET /batch/jobs/{id} |
| `lambda_job_logs` | `modules/lambda/lambda_job_logs` | Handles GET /batch/jobs/{id}/logs |
| `lambda_job_results` | `modules/lambda/lambda_job_results` | Handles GET /batch/jobs/{id}/results |
| `lambda_job_history_list` | `modules/lambda/lambda_job_history_list` | Handles GET /batch/jobs/history_list |
| `api_gateway` | `modules/api_gateway` | REST API with all routes, Lambda integrations, CORS, and auto-redeployment trigger |
| `api_key_usage_plan` | `modules/api_key_usage_plan` | API key and usage plan with throttling and optional quota |

---

## Inputs

All values are set in `terraform.tfvars`. Key variables:

| Name | Default | Description |
|---|---|---|
| `project_name` | — | Prefix for all resource names (`lifewatch`) |
| `region` | — | AWS region (`eu-west-1`) |
| `container_image` | — | ECR image URI used by both Fargate and EC2 job definitions |
| `batch_execution_role_arn` | — | Pre-existing ECS task execution role ARN |
| `vpc_cidr` | — | VPC CIDR block |
| `fargate_*` | various | Fargate compute and job sizing |
| `ec2_*` | various | EC2 compute and job sizing |
| `stage_name` | `"dev"` | API Gateway stage name |
| `api_key_name` | `"lifewatch-api-key"` | Name of the API key resource |
| `usage_plan_name` | `"lifewatch-usage-plan"` | Name of the usage plan resource |
| `burst_limit` | `5` | Max concurrent requests above the steady-state rate |
| `rate_limit` | `10` | Steady-state requests per second |
| `quota_limit` | `null` | Max requests per quota period — leave null to disable |
| `quota_offset` | `0` | Requests subtracted from quota at period start |
| `quota_period` | `"WEEK"` | Quota reset cadence: `DAY`, `WEEK`, or `MONTH` |

See `variables.tf` for the full list with descriptions and defaults.

---

## Outputs

| Name | Description |
|---|---|
| `api_gateway_url` | Base URL for the API — append `/batch/jobs` to call it |
| `api_key` | API key value (sensitive — use `terraform output -raw api_key`) |
| `api_key_id` | ID of the API key resource |
| `usage_plan_id` | ID of the API Gateway usage plan |
| `api_deployment_id` | ID of the active API Gateway deployment |
| `s3_bucket_name` | Name of the S3 payloads bucket |
| `fargate_job_queue_name` | Fargate queue name (useful for manual job submission) |
| `ec2_job_queue_name` | EC2 queue name (useful for manual job submission) |
| `fargate_job_definition_name` | Fargate job definition name |
| `ec2_job_definition_name` | EC2 job definition name |

---

## Remote state

State is stored in S3 with DynamoDB locking:

| Setting | Value |
|---|---|
| Bucket | `lifewatch-terraform-state-eu-west-1` |
| Key | `lifewatch-high-compute/dev/terraform.tfstate` |
| Region | `eu-west-1` |
| Lock table | `lifewatch-terraform-locks` |
