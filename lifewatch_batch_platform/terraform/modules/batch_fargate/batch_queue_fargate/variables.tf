variable "project_name" {
  description = "Project name prefix used for resource naming and tagging."
  type        = string
}

variable "compute_environment_arn" {
  description = "ARN of the Fargate compute environment to back this queue."
  type        = string
}

variable "priority" {
  description = "Queue scheduling priority. Higher value = higher priority."
  type        = number
  default     = 10
}

variable "runnable_timeout_seconds" {
  description = "Seconds a job may stay RUNNABLE before being cancelled due to compute misconfiguration."
  type        = number
  default     = 600
}

variable "tags" {
  description = "Map of tags applied to all resources in this module."
  type        = map(string)
  default     = {}
}

variable "profile_name" {
  type = string
}
