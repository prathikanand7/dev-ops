variable "project_name" {
  description = "Project name prefix used for resource naming and tagging. Combined with the AWS account ID to form a globally unique bucket name."
  type        = string
}

variable "tags" {
  description = "Map of tags applied to all resources in this module."
  type        = map(string)
  default     = {}
}
