# API Gateway Module

Creates the Lifewatch Batch API.

Routes:

POST /batch/jobs  
GET /batch/jobs/{job_id}  
GET /batch/jobs/{job_id}/logs  
GET /batch/jobs/{job_id}/results

Each route integrates with a Lambda function.

## Usage

```tf
module "api_gateway" {
source = "../../modules/api_gateway"

project_name = "lifewatch"
stage_name = "dev"

batch_trigger_lambda_arn = module.lambda.batch_trigger_arn
job_status_lambda_arn = module.lambda.job_status_arn
job_logs_lambda_arn = module.lambda.job_logs_arn
job_results_lambda_arn = module.lambda.job_results_arn
}
```
