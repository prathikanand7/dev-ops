# Module: lambda_batch_trigger

Deploys the **batch trigger** Lambda function, which receives the API Gateway `POST /batch/jobs` request, uploads the payload to S3, and submits a job to the appropriate Batch queue.

## Resources

| Resource | Description |
|---|---|
| `aws_lambda_function.batch_trigger` | Lambda function (`lambda_function.lambda_handler`) |
| `aws_lambda_permission.apigw` | Grants API Gateway permission to invoke the function |

## Usage

```hcl
module "lambda_batch_trigger" {
  source = "./modules/lambda_batch_trigger"

  project_name    = "lifewatch"
  lambda_role_arn = module.lambda_iam.role_arn
  filename        = "lambda.zip"

  s3_bucket_name               = module.s3.bucket_name
  standard_job_queue_name      = module.batch_queue_fargate.job_queue_name
  standard_job_definition_name = module.batch_job_definition_fargate.job_definition_name
  ec2_job_queue_name           = module.batch_queue_ec2.job_queue_name
  ec2_job_definition_name      = module.batch_job_definition_ec2.job_definition_name

  tags = { Environment = "dev" }
}
```

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `project_name` | `string` | — | Prefix for resource naming |
| `lambda_role_arn` | `string` | — | ARN of the shared Lambda IAM role |
| `filename` | `string` | `lambda.zip` | Path to the deployment ZIP |
| `runtime` | `string` | `python3.11` | Lambda runtime |
| `s3_bucket_name` | `string` | — | S3 payload bucket name |
| `standard_job_queue_name` | `string` | — | Fargate job queue name |
| `standard_job_definition_name` | `string` | — | Fargate job definition name |
| `ec2_job_queue_name` | `string` | — | EC2 job queue name |
| `ec2_job_definition_name` | `string` | — | EC2 job definition name |

## Outputs

| Name | Description |
|---|---|
| `function_name` | Name of the Lambda function |
| `function_arn` | ARN of the Lambda function |
| `invoke_arn` | Invoke ARN for use in API Gateway integrations |
