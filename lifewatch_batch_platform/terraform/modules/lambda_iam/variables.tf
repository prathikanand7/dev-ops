variable "project_name" {
  description = "Project name prefix used for resource naming and tagging."
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 payload bucket the Lambda functions need read/write access to."
  type        = string
}

variable "tags" {
  description = "Map of tags applied to all resources in this module."
  type        = map(string)
  default     = {}
}
