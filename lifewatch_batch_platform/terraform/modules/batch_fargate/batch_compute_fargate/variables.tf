variable "project_name" {
  description = "Project name prefix used for resource naming and tagging."
  type        = string
}

variable "max_vcpus" {
  description = "Maximum number of vCPUs the Fargate compute environment can scale to."
  type        = number
  default     = 256
}

variable "subnet_ids" {
  description = "List of subnet IDs in which Fargate tasks will be launched."
  type        = list(string)
}

variable "security_group_ids" {
  description = "List of security group IDs to attach to Fargate tasks."
  type        = list(string)
}

variable "vpc_endpoint_dependency_ids" {
  description = <<-EOT
    Opaque list of resource IDs used only to create an explicit depends_on
    ordering on required VPC endpoints (S3, ECR DKR, ECR API, Logs).
    Pass the id attribute of each endpoint resource.
  EOT
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Map of tags applied to all resources in this module."
  type        = map(string)
  default     = {}
}

variable "profile_name" {
  type = string
}

variable "service_role_arn" {
  type = string
}
