################################
# API
################################

output "api_gateway_url" {
  description = "Base URL of the deployed API Gateway stage."
  value       = "https://${module.api_gateway.api_id}.execute-api.${var.region}.amazonaws.com/${var.stage_name}"
}

output "api_key" {
  description = "API key value for authenticating requests. Treat as a secret."
  value       = module.api_key_usage_plan.api_key_value
  sensitive   = true
}

output "api_key_id" {
  description = "ID of the API key resource."
  value       = module.api_key_usage_plan.api_key_id
}

output "usage_plan_id" {
  description = "ID of the API Gateway usage plan."
  value       = module.api_key_usage_plan.usage_plan_id
}

output "api_deployment_id" {
  description = "ID of the active API Gateway deployment."
  value       = module.api_gateway.deployment_id
}

################################
# S3
################################

output "s3_bucket_name" {
  description = "Name of the S3 batch payloads bucket."
  value       = module.s3_batch_payloads.bucket_name
}

################################
# Batch - Fargate
################################

output "fargate_compute_environment_arns" {
  description = "ARNs of the Fargate compute environments."
  value       = { for k, v in module.batch_compute_fargate : k => v.compute_environment_arn }
}

output "fargate_job_queue_names" {
  description = "Names of the Fargate job queues."
  value       = { for k, v in module.batch_queue_fargate : k => v.job_queue_name }
}

output "fargate_job_definition_names" {
  description = "Names of the Fargate job definitions."
  value       = { for k, v in module.batch_job_definition_fargate : k => v.job_definition_name }
}

################################
# Batch - EC2
################################

output "ec2_compute_environment_arns" {
  description = "ARNs of the EC2 compute environments."
  value       = { for k, v in module.batch_compute_ec2 : k => v.compute_environment_arn }
}

output "ec2_job_queue_names" {
  description = "Names of the EC2 job queues."
  value       = { for k, v in module.batch_queue_ec2 : k => v.job_queue_name }
}

output "ec2_job_definition_names" {
  description = "Names of the EC2 job definitions."
  value       = { for k, v in module.batch_job_definition_ec2 : k => v.job_definition_name }
}

################################
# Lambda
################################

output "lambda_batch_trigger_arn" {
  description = "ARN of the batch trigger Lambda function."
  value       = module.lambda_batch_trigger.function_arn
}

output "lambda_job_status_arn" {
  description = "ARN of the job status Lambda function."
  value       = module.lambda_job_status.function_arn
}

output "lambda_job_logs_arn" {
  description = "ARN of the job logs Lambda function."
  value       = module.lambda_job_logs.function_arn
}

output "lambda_job_results_arn" {
  description = "ARN of the job results Lambda function."
  value       = module.lambda_job_results.function_arn
}

output "lambda_job_history_list_arn" {
  description = "ARN of the history list Lambda function."
  value       = module.lambda_job_history_list.function_arn
}
