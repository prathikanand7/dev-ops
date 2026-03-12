# Module: lambda_iam

Creates the **shared IAM role and policy** used by all four Lifewatch Lambda functions.

Separating IAM into its own module avoids duplicating the role across each function module and makes permission changes easy to apply in one place.

## Resources

| Resource | Description |
|---|---|
| `aws_iam_role.lambda` | IAM role assumed by all Lambda functions |
| `aws_iam_role_policy.lambda` | Inline policy granting S3, Batch, and CloudWatch Logs access |

## Permissions granted

| Service | Actions |
|---|---|
| S3 | `ListBucket`, `GetObject`, `PutObject` on the payload bucket |
| Batch | `SubmitJob`, `DescribeJobs` |
| CloudWatch Logs | `CreateLogGroup`, `CreateLogStream`, `PutLogEvents`, `GetLogEvents`, `DescribeLogStreams` |

## Usage

```hcl
module "lambda_iam" {
  source = "./modules/lambda_iam"

  project_name  = "lifewatch"
  s3_bucket_arn = module.s3.bucket_arn

  tags = { Environment = "dev" }
}
```

Pass the output to each function module:

```hcl
module "lambda_batch_trigger" {
  source = "./modules/lambda_batch_trigger"

  lambda_role_arn = module.lambda_iam.role_arn
  ...
}
```

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `project_name` | `string` | — | Prefix for resource names and tags |
| `s3_bucket_arn` | `string` | — | ARN of the S3 payload bucket |
| `tags` | `map(string)` | `{}` | Tags applied to all resources |

## Outputs

| Name | Description |
|---|---|
| `role_arn` | ARN of the shared Lambda IAM role |
| `role_name` | Name of the shared Lambda IAM role |
