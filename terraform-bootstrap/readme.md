# Terraform Bootstrap

Bootstrap stack for shared Terraform remote state resources.
This configuration allows us to store Terraform state on AWS S3, which in turn allows us to collaborate more easily, as there is a single point of truth for the state of the infrastructure.
This configuration allows us to store Terraform state on AWS S3, which in turn allows us to collaborate more easily, as there is a single point of truth for the state of the infrastructure.

## Purpose

This configuration creates:

- an S3 bucket for Terraform state storage (`lifewatch-terraform-state-eu-west-1`);
- a DynamoDB table for state locking (`lifewatch-terraform-locks`);
- an S3 bucket policy granting access to the IAM principals listed in `variables.tf`.

## Files

- `provider.tf`: AWS provider configuration.
- `main.tf`: Terraform and provider version constraints.
- `bucket.tf`: S3 state bucket, versioning, and encryption.
- `bucket_policy.tf`: IAM principal access policy for the state bucket.
- `dynamodb.tf`: lock table definition.
- `variables.tf`: configurable values (region, bucket name, table name, authorised principals).

## Usage

```bash
cd terraform-bootstrap
terraform init
terraform apply
```

## Backend Example For Environment Stacks

```hcl
terraform {
  backend "s3" {
    bucket         = "lifewatch-terraform-state-eu-west-1"
    key            = "lifewatch-high-compute/dev/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "lifewatch-terraform-locks"
    encrypt        = true
  }
}
```

## Operational Notes

- Terraform state can contain sensitive values; treat bucket access as privileged.
- Use distinct backend `key` values per environment (for example `dev`, `staging`, `prod`).
