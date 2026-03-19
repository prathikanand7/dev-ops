################################
# Global
################################

variable "project_name" {
  description = "Project name prefix applied to all resource names and tags."
  type        = string
}

variable "region" {
  description = "AWS region to deploy all resources into."
  type        = string
}

variable "tags" {
  description = "Map of tags applied to all resources."
  type        = map(string)
  default     = {}
}

################################
# VPC
################################

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
}

variable "public_subnet_a_cidr" {
  description = "CIDR block for public subnet A."
  type        = string
}

variable "public_subnet_b_cidr" {
  description = "CIDR block for public subnet B."
  type        = string
}

variable "private_subnet_a_cidr" {
  description = "CIDR block for private subnet A."
  type        = string
}

variable "private_subnet_b_cidr" {
  description = "CIDR block for private subnet B."
  type        = string
}

################################
# Batch - shared
################################

variable "container_image" {
  description = "Full ECR image URI used by both Fargate and EC2 job definitions."
  type        = string
}

variable "batch_execution_role_arn" {
  description = "ARN of the ECS task execution role used by the Fargate job definition to pull images and ship logs."
  type        = string
}

################################
# Batch - Fargate
################################

variable "fargate_max_vcpus" {
  description = "Maximum vCPUs for the Fargate compute environment."
  type        = number
  default     = 256
}

variable "fargate_vcpus" {
  description = "vCPUs allocated per Fargate job."
  type        = number
  default     = 1
}

variable "fargate_memory_mib" {
  description = "Memory (MiB) allocated per Fargate job."
  type        = number
  default     = 8192
}

variable "fargate_ephemeral_storage_gib" {
  description = "Ephemeral storage (GiB) per Fargate task."
  type        = number
  default     = 21
}

variable "fargate_job_timeout_seconds" {
  description = "Timeout duration of a job. Job is CANCELLED after timeout expires."
  type        = number
  default     = 7200 // 2 hours
}

################################
# Batch - EC2
################################

variable "ec2_max_vcpus" {
  description = "Maximum vCPUs for the EC2 compute environment."
  type        = number
  default     = 256
}

variable "ec2_instance_types" {
  description = "EC2 instance types the Batch environment may launch."
  type        = list(string)
  default     = ["m6i.2xlarge", "m6i.4xlarge", "m5.2xlarge", "m5.4xlarge"]
}

variable "ec2_ebs_volume_size_gb" {
  description = "Root EBS volume size (GiB) for EC2 Batch instances."
  type        = number
  default     = 200
}

variable "ec2_vcpus" {
  description = "vCPUs allocated per EC2 job."
  type        = number
  default     = 2
}

variable "ec2_memory_mib" {
  description = "Memory (MiB) allocated per EC2 job."
  type        = number
  default     = 16384
}

variable "ec2_job_timeout_seconds" {
  description = "Timeout duration of a job. Job is CANCELLED after timeout expires."
  type        = number
  default     = 7200 // 2 hours
}

################################
# Lambda
################################

variable "lambda_trigger_filename" {
  description = "Path to the batch trigger Lambda deployment ZIP."
  type        = string
  default     = "lambda.zip"
}

variable "lambda_status_filename" {
  description = "Path to the job status Lambda deployment ZIP."
  type        = string
  default     = "status_lambda.zip"
}

variable "lambda_logs_filename" {
  description = "Path to the job logs Lambda deployment ZIP."
  type        = string
  default     = "logs_lambda.zip"
}

variable "lambda_results_filename" {
  description = "Path to the job results Lambda deployment ZIP."
  type        = string
  default     = "results_lambda.zip"
}

variable "lambda_history_list_filename" {
  description = "Path to the job history list Lambda deployment ZIP."
  type        = string
  default     = "history_list_lambda.zip"
}

################################
# API Gateway
################################

variable "stage_name" {
  description = "API Gateway stage name."
  type        = string
  default     = "dev"
}

variable "api_key_name" {
  description = "Name of the API Gateway API key."
  type        = string
  default     = "lifewatch-api-key"
}

variable "usage_plan_name" {
  description = "Name of the API Gateway usage plan."
  type        = string
  default     = "lifewatch-usage-plan"
}

variable "usage_plan_description" {
  description = "Description of the API Gateway usage plan."
  type        = string
  default     = "Usage plan for Lifewatch REST API"
}

variable "burst_limit" {
  description = "API Gateway usage plan burst limit (max concurrent requests above rate_limit)."
  type        = number
  default     = 5
}

variable "rate_limit" {
  description = "API Gateway usage plan steady-state rate limit (requests per second)."
  type        = number
  default     = 10
}
