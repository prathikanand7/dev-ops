variable "project_name" {
  description = "Project name prefix used for resource naming."
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN of the IAM role the Lambda function assumes. Use the output of the lambda_iam module."
  type        = string
}

variable "filename" {
  description = "Path to the deployment ZIP archive for this function."
  type        = string
  default     = "history_list_lambda.zip"
}

variable "runtime" {
  description = "Lambda runtime identifier."
  type        = string
  default     = "python3.11"
}

variable "timeout" {
  description = "Function timeout in seconds."
  type        = number
  default     = 10
}

variable "s3_bucket_name" {
  description = "Name (not ARN) of the S3 payload bucket passed to the function as an environment variable."
  type        = string
}
