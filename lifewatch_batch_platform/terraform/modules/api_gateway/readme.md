# Module: `api_gateway`

Provisions an AWS API Gateway REST API for the Lifewatch batch platform.

This module is primarily **OpenAPI-driven**:

- Route/method/integration definitions come from `openapi.yaml`.
- Terraform still manages deployment/stage and gateway-level response behavior.

---

## Implementation model

1. `aws_api_gateway_rest_api` imports the full API spec from `openapi.yaml` via `templatefile(...)`.
2. `aws_api_gateway_deployment` redeploys when the rendered OpenAPI body changes.
3. `aws_api_gateway_stage` publishes the deployment to the configured stage.
4. `aws_api_gateway_gateway_response` resources add CORS headers on API Gateway-level error paths.

---

## Resources created

| Resource | Description |
|---|---|
| `aws_api_gateway_rest_api` | The REST API with multipart/form-data binary support |
| `aws_api_gateway_resource` | Routes: `/batch`, `/batch/jobs`, `/batch/jobs/{job_id}`, `/batch/jobs/{job_id}/logs`, `/batch/jobs/{job_id}/results`, `/batch/jobs/history_list` |
| `aws_api_gateway_method` | `POST /batch/jobs`, `GET` on status/logs/results/history_list, `OPTIONS` on all routes |
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
| `batch_trigger_lambda_arn` | `string` | yes | Invoke ARN for `POST /batch/jobs` |
| `job_status_lambda_arn` | `string` | yes | Invoke ARN for `GET /batch/jobs/{job_id}` |
| `job_logs_lambda_arn` | `string` | yes | Invoke ARN for `GET /batch/jobs/{job_id}/logs` |
| `job_results_lambda_arn` | `string` | yes | Invoke ARN for `GET /batch/jobs/{job_id}/results` |
| `job_history_list_lambda_arn` | `string` | yes | Invoke ARN for `GET /batch/jobs/history_list` |

---

## Outputs

| Name | Description |
|---|---|
| `api_id` | ID of the REST API |
| `stage_name` | Name of the deployed stage |
| `invoke_url` | Base invoke URL of the stage |
| `deployment_id` | ID of the active deployment |

---

## CORS behavior

CORS is handled in two layers:

1. **Preflight CORS (route-level, from OpenAPI)**
   - Each route defines `OPTIONS` with a `MOCK` integration.
   - Response headers include `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, and `Access-Control-Allow-Headers`.

2. **Error CORS (gateway-level, from Terraform resources)**
   - Gateway responses add CORS headers for API Gateway-generated errors (e.g. missing auth token, missing resource).

Current defaults:

- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Headers: Content-Type,x-api-key,Authorization`
- `Access-Control-Allow-Methods: OPTIONS,GET,POST`

> Restrict `Access-Control-Allow-Origin` to trusted frontend origins for production.

---

## Authentication

- Functional routes in `openapi.yaml` use `ApiKeyAuth` (`x-api-key` header).
- `OPTIONS` routes are unauthenticated (`security: []`) for browser preflight support.
- Attach API keys and usage plans via the separate `api_key_usage_plan` module.

---

## Usage example

```hcl
module "api_gateway" {
  source = "./modules/api_gateway"

  project_name              = "lifewatch"
  stage_name                = "dev"
  batch_trigger_lambda_arn  = module.lambda_batch.invoke_arn
  job_status_lambda_arn     = module.lambda_status.invoke_arn
  job_logs_lambda_arn       = module.lambda_logs.invoke_arn
  job_results_lambda_arn    = module.lambda_results.invoke_arn
  job_history_list_lambda_arn = module.lambda_history_list.invoke_arn
}

module "api_key_usage_plan" {
  source = "./modules/api_key_usage_plan"

  lifewatch_key_name = "lifewatch-api-key"
  usage_plan_name    = "lifewatch-usage-plan"
  api_id             = module.api_gateway.api_id
  stage_name         = module.api_gateway.stage_name
}
```
