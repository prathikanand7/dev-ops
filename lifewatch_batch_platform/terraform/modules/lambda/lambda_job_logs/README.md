# Module: lambda_job_logs

Deploys the **job logs** Lambda function, which handles `GET /batch/jobs/{job_id}/logs` and retrieves CloudWatch log output for a completed or running Batch job.

## Resources

| Resource | Description |
|---|---|
| `aws_lambda_function.job_logs` | Lambda function (`logs.lambda_handler`) |
| `aws_lambda_permission.apigw` | Grants API Gateway permission to invoke the function |

## Usage

```hcl
module "lambda_job_logs" {
  source = "./modules/lambda_job_logs"

  project_name    = "lifewatch"
  lambda_role_arn = module.lambda_iam.role_arn
  filename        = "logs_lambda.zip"
  s3_bucket_name  = module.s3.bucket_name

  tags = { Environment = "dev" }
}
```

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `project_name` | `string` | — | Prefix for resource naming |
| `lambda_role_arn` | `string` | — | ARN of the shared Lambda IAM role |
| `filename` | `string` | `logs_lambda.zip` | Path to the deployment ZIP |
| `runtime` | `string` | `python3.11` | Lambda runtime |
| `timeout` | `number` | `10` | Function timeout in seconds |
| `s3_bucket_name` | `string` | — | S3 payload bucket name |

## Outputs

| Name | Description |
|---|---|
| `function_name` | Name of the Lambda function |
| `function_arn` | ARN of the Lambda function |
| `invoke_arn` | Invoke ARN for use in API Gateway integrations |
