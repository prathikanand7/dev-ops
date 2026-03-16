variable "project_name" {
  description = "Project name prefix used for resource naming."
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket to grant jobs access to."
  type        = string
}

variable "tags" {
  description = "A map of tags to add to all resources."
  type        = map(string)
  default     = {}
}
