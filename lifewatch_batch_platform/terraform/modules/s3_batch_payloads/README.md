# Module: s3_batch_payloads

Creates the **S3 bucket** used to store job input payloads and output results for AWS Batch jobs.

The bucket name is automatically made globally unique by appending the AWS account ID.

## Resources

| Resource | Description |
|---|---|
| `data.aws_caller_identity.current` | Looks up the current AWS account ID for bucket naming |
| `aws_s3_bucket.batch_payloads` | S3 bucket for Batch job payloads and results |

## Usage

```hcl
module "s3_batch_payloads" {
  source = "./modules/s3_batch_payloads"

  project_name = "lifewatch"
  tags         = { Environment = "dev" }
}
```

Pass the outputs to other modules that need bucket access:

```hcl
module "lambda_iam" {
  source        = "./modules/lambda_iam"
  s3_bucket_arn = module.s3_batch_payloads.bucket_arn
  ...
}

module "lambda_batch_trigger" {
  source         = "./modules/lambda_batch_trigger"
  s3_bucket_name = module.s3_batch_payloads.bucket_name
  ...
}

module "batch_job_definition_fargate" {
  source        = "./modules/batch_job_definition_fargate"
  s3_bucket_arn = module.s3_batch_payloads.bucket_arn
  ...
}
```

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `project_name` | `string` | — | Prefix for the bucket name and tags |
| `tags` | `map(string)` | `{}` | Tags applied to all resources |

## Outputs

| Name | Description |
|---|---|
| `bucket_name` | Name of the S3 bucket (used as an env var in Lambda functions) |
| `bucket_arn` | ARN of the S3 bucket (used in IAM policies) |
