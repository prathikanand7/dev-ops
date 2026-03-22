# Terraform Bootstrap

Bootstrap stack for shared Terraform remote state resources.Expand commentComment on line R3Resolved
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

### 3. IAM Users & Permissions

Terraform requires specific permissions to interact with the S3 bucket and DynamoDB lock table. Assign the following IAM policy to all users who need access to Terraform state:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::lifewatch-terraform-state-eu-west-1"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::lifewatch-terraform-state-eu-west-1/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:eu-west-1:020858641931:table/terraform-locks"
    }
  ]
}
```

> This policy is based on the guide by Deepesh Jaiswal: [Setting up Terraform with S3 Backend and DynamoDB Locking](https://medium.com/@deepeshjaiswal6734/setting-up-terraform-with-s3-backend-and-dynamodb-locking-1e4b69e0b3cd)

Important: Assign this policy to all IAM users who will run Terraform against this backend.

---

## Usage

1. Initialize and apply the bootstrap

```bash
cd bootstrap
terraform init
terraform apply
```

- This creates the S3 bucket, DynamoDB table, and applies the bucket policy to allow your IAM users to access the state.

2. Configure your main Terraform project

We have added a backend block pointing to the S3 bucket and DynamoDB lock table:

```hcl
terraform {
  backend "s3" {
    bucket         = "lifewatch-terraform-state-eu-west-1"
    key            = "project/dev/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

3. Run Terraform commands normally

```bash
terraform init
terraform plan
terraform apply
```

- Terraform will automatically create and update the state in S3 and handle locks in DynamoDB.

---

## Operational Notes

- Terraform state can contain sensitive values; treat bucket access as privileged.
- Use distinct backend `key` values per environment (for example `dev`, `staging`, `prod`).