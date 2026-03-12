# Module: batch_compute_fargate

Creates an AWS Batch **managed Fargate compute environment**.

## Resources

| Resource | Description |
|---|---|
| `aws_batch_compute_environment.fargate` | Managed Fargate compute environment |

## Usage

```hcl
module "batch_compute_fargate" {
  source = "./modules/batch_compute_fargate"

  project_name       = "lifewatch"
  max_vcpus          = 256
  subnet_ids         = module.vpc.public_subnet_ids
  security_group_ids = [module.security_groups.batch_sg_id]

  vpc_endpoint_dependency_ids = [
    module.vpc_endpoints.s3_endpoint_id,
    module.vpc_endpoints.ecr_dkr_endpoint_id,
    module.vpc_endpoints.ecr_api_endpoint_id,
    module.vpc_endpoints.logs_endpoint_id,
  ]

  tags = { Environment = "dev" }
}
```

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `project_name` | `string` | — | Prefix for resource names and tags |
| `max_vcpus` | `number` | `256` | Maximum vCPUs the environment can scale to |
| `subnet_ids` | `list(string)` | — | Subnets for Fargate task placement |
| `security_group_ids` | `list(string)` | — | Security groups attached to Fargate tasks |
| `vpc_endpoint_dependency_ids` | `list(string)` | `[]` | IDs of VPC endpoints to depend on before creation |
| `tags` | `map(string)` | `{}` | Tags applied to all resources |

## Outputs

| Name | Description |
|---|---|
| `compute_environment_arn` | ARN of the Fargate compute environment |
| `compute_environment_name` | Name of the Fargate compute environment |
