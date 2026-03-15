---

# Terraform S3 Backend & DynamoDB Lock Setup

This repository contains the Terraform bootstrap configuration for setting up a remote backend for Terraform using S3 and DynamoDB locking.

It ensures that:

- Terraform state is stored remotely in a versioned and encrypted S3 bucket.
- Concurrent Terraform runs are prevented using a DynamoDB table for state locking.
- Only authorized IAM users can access and modify Terraform state.

---

## Components

### 1. S3 Bucket

- Stores Terraform state files (`.tfstate`).
- Features enabled:
  - Versioning – protects against accidental deletion.
  - Server-side encryption (AES256) – encrypts state at rest.

- Access is restricted via bucket policy to specific IAM users.

### 2. DynamoDB Table

- Used for state locking, preventing multiple users or CI jobs from modifying the state simultaneously.
- Table has a single primary key (`LockID`).
- Terraform automatically creates and deletes lock entries during `apply`.

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

## Notes & Best Practices

- Do not share the bucket with untrusted users; Terraform state may contain sensitive information (passwords, secrets, ARNs).
- Use different keys per environment (`dev`, `staging`, `prod`) in the same bucket for separation.
- Enable DynamoDB locking to prevent simultaneous Terraform runs.
