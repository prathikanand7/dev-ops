# Module: `vpc_endpoints`

Creates private AWS service connectivity using VPC endpoints for Batch compute workloads running in private subnets.

## Endpoints provisioned

| Endpoint | Type | Justification |
|---|---|---|
| S3 | Gateway | Free — routes all worker.py S3 traffic privately at no cost |
| ECS | Interface | Required for job scheduling — without it Batch cannot register or start tasks |
| ECS Agent | Interface | Required for EC2 job status reporting — without it instances cannot receive instructions or report task state |

## Endpoints intentionally omitted

| Endpoint | Reason for omission |
|---|---|
| ECR API | Fixed cost (~$7/month) exceeds variable NAT cost at expected job frequency (10-100 jobs/month). Image auth calls route via NAT gateway at negligible cost. |
| ECR DKR | Fixed cost (~$7/month) exceeds variable NAT cost at expected job frequency. Image pulls route via NAT at $0.048/GB. |
| CloudWatch Logs | No functional impact — logs ship via NAT gateway fallback. Fixed cost exceeds variable NAT cost at expected job frequency. |
| ECS Telemetry | Retained during initial platform operation for right-sizing visibility. Candidate for removal once workload patterns are established. |

NAT gateway remains provisioned as the fallback path for ECR image pulls, CloudWatch log shipping, and `mamba env update` calls to public package repositories.

## Interface endpoints

All interface endpoints are placed in the private subnets across both availability zones, provisioning one ENI per subnet per endpoint. `private_dns_enabled = true` is set on all interface endpoints so that AWS service hostnames resolve transparently to private ENI IP addresses inside the VPC without requiring any changes to application code.

## Usage

```hcl
module "vpc_endpoints" {
  source = "../../modules/vpc_endpoints"

  project_name            = "lifewatch"
  region                  = "eu-west-1"
  vpc_id                  = module.vpc.vpc_id
  private_subnet_ids      = module.vpc.private_subnets
  private_route_table_id  = module.vpc.private_route_table_id
  endpoint_security_group = module.security_groups.endpoint_security_group_id

  tags = var.tags
}
```

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `project_name` | `string` | yes | Prefix for all resource names |
| `region` | `string` | yes | AWS region to deploy endpoints into |
| `vpc_id` | `string` | yes | ID of the VPC |
| `private_subnet_ids` | `list(string)` | yes | Private subnet IDs for interface endpoint ENIs |
| `private_route_table_id` | `string` | yes | Private route table ID for S3 gateway endpoint |
| `endpoint_security_group` | `string` | yes | Security group ID for interface endpoints |
| `tags` | `map(string)` | no | Tags applied to all resources |

## Outputs

| Name | Description |
|---|---|
| `s3_endpoint_id` | ID of the S3 gateway endpoint |
| `ecs_endpoint_id` | ID of the ECS interface endpoint |
| `ecs_agent_endpoint_id` | ID of the ECS agent interface endpoint |
