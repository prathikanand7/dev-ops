# Module: `api_gateway`

Provisions an AWS API Gateway REST API with Lambda integrations, CORS preflight support, and a versioned deployment stage.

---

## Resources created

| Resource | Description |
|---|---|
| `aws_api_gateway_rest_api` | The REST API with multipart/form-data binary support |
| `aws_api_gateway_resource` | Routes: `/batch`, `/batch/jobs`, `/batch/jobs/{job_id}`, `/batch/jobs/{job_id}/logs`, `/batch/jobs/{job_id}/results` |
| `aws_api_gateway_method` | `POST /batch/jobs`, `GET` on status/logs/results, `OPTIONS` on all routes |
| `aws_api_gateway_integration` | `AWS_PROXY` Lambda integrations for all functional routes; `MOCK` integrations for CORS preflight |
| `aws_api_gateway_method_response` | `200` responses declaring CORS headers on all OPTIONS routes |
| `aws_api_gateway_integration_response` | Injects `Access-Control-Allow-*` headers into preflight responses |
| `aws_api_gateway_deployment` | Versioned deployment with sha1 change-detection trigger |
| `aws_api_gateway_stage` | Deploys the API to the configured stage name |

---

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `project_name` | `string` | yes | Prefix used to name the REST API (`<project_name>-api`) |
| `stage_name` | `string` | yes | Stage name to deploy to (e.g. `dev`, `staging`, `prod`) |
| `batch_trigger_lambda_arn` | `string` | yes | Invoke ARN of the Lambda for `POST /batch/jobs` |
| `job_status_lambda_arn` | `string` | yes | Invoke ARN of the Lambda for `GET /batch/jobs/{job_id}` |
| `job_logs_lambda_arn` | `string` | yes | Invoke ARN of the Lambda for `GET /batch/jobs/{job_id}/logs` |
| `job_results_lambda_arn` | `string` | yes | Invoke ARN of the Lambda for `GET /batch/jobs/{job_id}/results` |
| `job_history_list_lambda_arn` | `string` | yes | Invoke ARN of the Lambda for `GET /batch/jobs/history_list` |

---

## Outputs

| Name | Description |
|---|---|
| `api_id` | ID of the REST API — pass to the `api_key_usage_plan` module |
| `stage_name` | Name of the deployed stage — pass to the `api_key_usage_plan` module |
| `invoke_url` | Full base URL for calling the API (e.g. `https://<id>.execute-api.<region>.amazonaws.com/<stage>`) |
| `deployment_id` | ID of the active deployment resource |

---

## CORS

All functional routes expose an `OPTIONS` method backed by a `MOCK` integration so browsers can complete preflight checks without invoking Lambda.

> **Note:** `Access-Control-Allow-Origin` is currently set to `*`. Restrict this to your frontend origin(s) before deploying to production.

Allowed headers: `Content-Type`, `x-api-key`, `Authorization`

---

## Authentication

All methods set `api_key_required = true`. An API key and usage plan must be attached to the stage via the `api_key_usage_plan` module.

---

## Usage example

```hcl
module "api_gateway" {
  source = "./modules/api_gateway"

  project_name             = "lifewatch"
  stage_name               = "dev"
  batch_trigger_lambda_arn = module.lambda_batch.invoke_arn
  job_status_lambda_arn    = module.lambda_status.invoke_arn
  job_logs_lambda_arn      = module.lambda_logs.invoke_arn
  job_results_lambda_arn   = module.lambda_results.invoke_arn
  job_history_list_lambda_arn   = module.lambda_history_list.invoke_arn
}

module "api_key_usage_plan" {
  source = "./modules/api_key_usage_plan"

  lifewatch_key_name = "lifewatch-api-key"
  usage_plan_name    = "lifewatch-usage-plan"
  api_id             = module.api_gateway.api_id
  stage_name         = module.api_gateway.stage_name
}
```
