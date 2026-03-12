# Terraform VPC Module

Creates a production-ready VPC including:

- Internet Gateway
- Public Subnets
- Private Subnets
- NAT Gateway
- Public Route Table
- Private Route Table

Architecture:

VPC  
├── Public Subnets  
│ ├── NAT Gateway  
│ └── Load Balancers  
│  
└── Private Subnets  
 ├── AWS Batch
├── ECS / Containers
└── Internal Services

## Usage

module "vpc" {

source = "../../modules/vpc"

project_name = "lifewatch"  
region = "eu-west-1"

vpc_cidr = "10.0.0.0/16"

public_subnet_a_cidr = "10.0.1.0/24"  
public_subnet_b_cidr = "10.0.2.0/24"

private_subnet_a_cidr = "10.0.11.0/24"  
private_subnet_b_cidr = "10.0.12.0/24"

tags = {
Environment = "dev"
Project = "lifewatch"
}

}

## Outputs

- VPC ID
- Public Subnets
- Private Subnets
- Route Tables
- NAT Gateway
