variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
}

variable "public_subnet_a_cidr" {
  description = "CIDR for public subnet A"
  type        = string
}

variable "public_subnet_b_cidr" {
  description = "CIDR for public subnet B"
  type        = string
}

variable "private_subnet_a_cidr" {
  description = "CIDR for private subnet A"
  type        = string
}

variable "private_subnet_b_cidr" {
  description = "CIDR for private subnet B"
  type        = string
}

variable "internet_cidr" {
  description = "Default internet route"
  type        = string
  default     = "0.0.0.0/0"
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}