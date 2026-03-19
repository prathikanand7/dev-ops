variable "project_name" {
  description = "Project name prefix used for resource naming and tagging."
  type        = string
}

variable "container_image" {
  description = "Full ECR image URI for the EC2 job container."
  type        = string
}

variable "container_command" {
  description = "Command passed to the container at startup."
  type        = list(string)
  default     = ["python", "worker.py"]
}

variable "vcpus" {
  description = "Number of vCPUs allocated to each EC2 job."
  type        = number
  default     = 2
}

variable "memory_mib" {
  description = "Memory (MiB) allocated to each EC2 job."
  type        = number
  default     = 16384
}

variable "job_timeout_seconds" {
  description = "Timeout duration of a job. Job is CANCELLED after timeout expires."
  type = number
  default = 7200 // 2 hours
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket the job role needs read/write access to."
  type        = string
}

variable "tags" {
  description = "Map of tags applied to all resources in this module."
  type        = map(string)
  default     = {}
}

variable "profile_name" {
  type = string
}

variable "job_role_arn" {
  type = string
}
