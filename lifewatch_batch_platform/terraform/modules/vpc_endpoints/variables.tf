variable "project_name" {
  description = "Project name prefix applied to all resource names and tags."
  type        = string
}

variable "region" {
  description = "AWS region to deploy endpoints into."
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC to create endpoints in."
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs to place interface endpoint ENIs into."
  type        = list(string)
}

variable "private_route_table_id" {
  description = "ID of the private route table to attach the S3 gateway endpoint to."
  type        = string
}

variable "endpoint_security_group" {
  description = "Security group ID to attach to interface endpoints."
  type        = string
}

variable "tags" {
  description = "Map of tags applied to all endpoint resources."
  type        = map(string)
  default     = {}
}
