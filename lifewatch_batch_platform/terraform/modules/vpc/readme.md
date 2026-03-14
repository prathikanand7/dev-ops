# Module: vpc

Creates the full VPC networking stack including public and private subnets across two availability zones, an internet gateway, a NAT gateway, and separate route tables for public and private traffic.

## Resources

| Resource | Description |
|---|---|
| `aws_vpc.main` | VPC with DNS support enabled |
| `aws_internet_gateway.igw` | Internet gateway attached to the VPC |
| `aws_subnet.public_a/b` | Public subnets in AZ a and b — instances get public IPs |
| `aws_subnet.private_a/b` | Private subnets in AZ a and b — no public IPs |
| `aws_eip.nat` | Elastic IP for the NAT gateway |
| `aws_nat_gateway.nat` | NAT gateway in public subnet a — routes private outbound traffic |
| `aws_route_table.public` | Routes `0.0.0.0/0` → internet gateway |
| `aws_route_table.private` | Routes `0.0.0.0/0` → NAT gateway |

## Usage

```hcl
module "vpc" {
  source = "../../modules/vpc"

  project_name          = "lifewatch"
  region                = "eu-west-1"
  vpc_cidr              = "10.0.0.0/16"
  public_subnet_a_cidr  = "10.0.103.0/24"
  public_subnet_b_cidr  = "10.0.102.0/24"
  private_subnet_a_cidr = "10.0.1.0/24"
  private_subnet_b_cidr = "10.0.2.0/24"

  tags = { Environment = "dev" }
}
```

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `project_name` | `string` | — | Prefix for resource names and tags |
| `region` | `string` | — | AWS region (used to construct AZ names) |
| `vpc_cidr` | `string` | — | CIDR block for the VPC |
| `public_subnet_a_cidr` | `string` | — | CIDR for public subnet in AZ a |
| `public_subnet_b_cidr` | `string` | — | CIDR for public subnet in AZ b |
| `private_subnet_a_cidr` | `string` | — | CIDR for private subnet in AZ a |
| `private_subnet_b_cidr` | `string` | — | CIDR for private subnet in AZ b |
| `internet_cidr` | `string` | `0.0.0.0/0` | Internet CIDR used in route tables |
| `tags` | `map(string)` | `{}` | Tags applied to all resources |

## Outputs

| Name | Description |
|---|---|
| `vpc_id` | VPC ID |
| `public_subnets` | List of both public subnet IDs |
| `private_subnets` | List of both private subnet IDs |
| `public_subnet_a_id` | Public subnet ID in AZ a |
| `public_subnet_b_id` | Public subnet ID in AZ b |
| `private_subnet_a_id` | Private subnet ID in AZ a |
| `private_subnet_b_id` | Private subnet ID in AZ b |
| `public_route_table_id` | Public route table ID |
| `private_route_table_id` | Private route table ID |
| `nat_gateway_id` | NAT gateway ID |
| `internet_gateway_id` | Internet gateway ID |
