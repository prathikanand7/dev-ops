# Module: `vpc_endpoints`

Creates private AWS service connectivity using VPC endpoints for Batch compute workloads running in private subnets.

## Endpoints provisioned

| Endpoint | Type    | Justification                                               |
| -------- | ------- | ----------------------------------------------------------- |
| S3       | Gateway | Free -routes all worker.py S3 traffic privately at no cost |

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

| Name                      | Type           | Required | Description                                    |
| ------------------------- | -------------- | -------- | ---------------------------------------------- |
| `project_name`            | `string`       | yes      | Prefix for all resource names                  |
| `region`                  | `string`       | yes      | AWS region to deploy endpoints into            |
| `vpc_id`                  | `string`       | yes      | ID of the VPC                                  |
| `private_subnet_ids`      | `list(string)` | yes      | Private subnet IDs for interface endpoint ENIs |
| `private_route_table_id`  | `string`       | yes      | Private route table ID for S3 gateway endpoint |
| `endpoint_security_group` | `string`       | yes      | Security group ID for interface endpoints      |
| `tags`                    | `map(string)`  | no       | Tags applied to all resources                  |

## Outputs

| Name             | Description                   |
| ---------------- | ----------------------------- |
| `s3_endpoint_id` | ID of the S3 gateway endpoint |
