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
  default     = "lambda.zip"
}

variable "runtime" {
  description = "Lambda runtime identifier."
  type        = string
  default     = "python3.11"
}

variable "s3_bucket_name" {
  description = "Name (not ARN) of the S3 payload bucket passed to the function as an environment variable."
  type        = string
}

variable "standard_job_queue_name" {
  description = "Name of the Fargate (standard) Batch job queue."
  type        = string
}

variable "standard_job_definition_name" {
  description = "Name of the Fargate (standard) Batch job definition."
  type        = string
}

variable "ec2_job_queue_name" {
  description = "Name of the EC2 200GB Batch job queue."
  type        = string
}

variable "ec2_job_definition_name" {
  description = "Name of the EC2 200GB Batch job definition."
  type        = string
}
