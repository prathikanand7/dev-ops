variable "project_name" {
  description = "Project name prefix used to name the REST API."
  type        = string
}

variable "stage_name" {
  description = "Name of the API Gateway stage to deploy (e.g. dev, staging, prod)."
  type        = string
}

variable "batch_trigger_lambda_arn" {
  description = "Invoke ARN of the Lambda that handles POST /batch/jobs."
  type        = string
}

variable "job_status_lambda_arn" {
  description = "Invoke ARN of the Lambda that handles GET /batch/jobs/{job_id}."
  type        = string
}

variable "job_logs_lambda_arn" {
  description = "Invoke ARN of the Lambda that handles GET /batch/jobs/{job_id}/logs."
  type        = string
}

variable "job_results_lambda_arn" {
  description = "Invoke ARN of the Lambda that handles GET /batch/jobs/{job_id}/results."
  type        = string
}
