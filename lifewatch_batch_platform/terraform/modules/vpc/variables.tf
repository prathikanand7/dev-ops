variable "project_name" {
  description = "Project name prefix used for resource naming and tagging."
  type        = string
}

variable "region" {
  description = "AWS region. Used to construct availability zone names (e.g. eu-west-1a)."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
}

variable "public_subnet_a_cidr" {
  description = "CIDR block for public subnet in AZ a."
  type        = string
}

variable "public_subnet_b_cidr" {
  description = "CIDR block for public subnet in AZ b."
  type        = string
}

variable "private_subnet_a_cidr" {
  description = "CIDR block for private subnet in AZ a."
  type        = string
}

variable "private_subnet_b_cidr" {
  description = "CIDR block for private subnet in AZ b."
  type        = string
}

variable "internet_cidr" {
  description = "CIDR block representing the internet. Almost always 0.0.0.0/0."
  type        = string
  default     = "0.0.0.0/0"
}

variable "tags" {
  description = "Map of tags applied to all resources in this module."
  type        = map(string)
  default     = {}
}
