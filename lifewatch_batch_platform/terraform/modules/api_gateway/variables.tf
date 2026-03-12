variable "project_name" {
  type = string
}

variable "stage_name" {
  type = string
}

variable "batch_trigger_lambda_arn" {
  type = string
}

variable "job_status_lambda_arn" {
  type = string
}

variable "job_logs_lambda_arn" {
  type = string
}

variable "job_results_lambda_arn" {
  type = string
}