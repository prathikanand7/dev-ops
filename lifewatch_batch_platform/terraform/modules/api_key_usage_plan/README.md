# Module: api_key_usage_plan

Creates an API Gateway **API key**, **usage plan**, and attaches them together. The usage plan is linked to an existing stage and enforces throttling limits.

The deployment and stage resources intentionally live in the `api_gateway` module — this module only needs the `api_id` and `stage_name` passed in as variables.

## Resources

| Resource | Description |
|---|---|
| `aws_api_gateway_api_key.this` | API key for authenticating requests |
| `aws_api_gateway_usage_plan.this` | Usage plan with throttle settings |
| `aws_api_gateway_usage_plan_key.this` | Attaches the key to the plan |

## Usage

```hcl
module "api_key_usage_plan" {
  source = "../../modules/api_key_usage_plan"

  lifewatch_key_name     = "lifewatch-api-key"
  api_id                 = module.api_gateway.api_id
  stage_name             = module.api_gateway.stage_name
  usage_plan_name        = "lifewatch-usage-plan"
  usage_plan_description = "Usage plan for Lifewatch REST API"
  burst_limit            = 5
  rate_limit             = 10
}
```

Retrieve the key after apply:
```bash
terraform output -raw api_key
```

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `lifewatch_key_name` | `string` | — | Name of the API key |
| `api_id` | `string` | — | REST API ID from the `api_gateway` module |
| `stage_name` | `string` | — | Stage name from the `api_gateway` module |
| `usage_plan_name` | `string` | — | Name of the usage plan |
| `usage_plan_description` | `string` | `""` | Description of the usage plan |
| `burst_limit` | `number` | `5` | Max concurrent requests above the rate limit |
| `rate_limit` | `number` | `10` | Steady-state requests per second |

## Outputs

| Name | Description |
|---|---|
| `api_key_value` | The API key value (sensitive) |
| `api_key_id` | ID of the API key resource |
| `usage_plan_id` | ID of the usage plan |
