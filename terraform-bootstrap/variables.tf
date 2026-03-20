variable "aws_region" {
  description = "AWS region for the S3 bucket and DynamoDB table"
  type        = string
  default     = "eu-west-1"
}

variable "terraform_users" {
  description = "List of IAM users who can access the Terraform state bucket"
  type        = list(string)
  default = [
    "arn:aws:iam::020858641931:user/KayleDevOps",
    "arn:aws:iam::020858641931:user/Prathik",
    "arn:aws:iam::020858641931:user/Giorgos",
    "arn:aws:iam::020858641931:user/Eneko"
  ]
}

variable "bucket_name" {
  description = "Name of the S3 bucket to store Terraform state (must be globally unique)"
  type        = string
  default     = "lifewatch-terraform-state-eu-west-1"
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name for Terraform state locking"
  type        = string
  default     = "lifewatch-terraform-locks"
}
