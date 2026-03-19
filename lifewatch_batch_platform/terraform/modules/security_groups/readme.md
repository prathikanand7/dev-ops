# Security Groups Module

Creates security groups for:

- AWS Batch compute environments
- VPC Interface Endpoints

Security model:

Batch SG
|
| HTTPS
v
Endpoint SG
|
v
AWS services

Batch instances cannot directly access other VPC resources.

## Usage

module "security_groups" {
source = "../../modules/security_groups"

project_name = "lifewatch"
vpc_id = module.vpc.vpc_id
}
