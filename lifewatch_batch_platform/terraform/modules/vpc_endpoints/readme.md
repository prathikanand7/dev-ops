# VPC Endpoints Module

Creates private AWS service connectivity using VPC endpoints.

Services:

- S3 (Gateway)
- ECR API
- ECR Docker
- CloudWatch Logs
- ECS
- ECS Agent
- ECS Telemetry

Interface endpoints are placed in **private subnets**.

## Usage

```tf
module "vpc_endpoints" {

source = "../../modules/vpc_endpoints"

project_name = "lifewatch"
region = "eu-west-1"

vpc_id = module.vpc.vpc_id

private_subnet_ids = module.vpc.private_subnets

private_route_table_id = module.vpc.private_route_table_id

endpoint_security_group = aws_security_group.vpc_endpoint.id

}
```
