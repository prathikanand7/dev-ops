output "job_definition_arn" {
  description = "ARN of the EC2 job definition."
  value       = aws_batch_job_definition.ec2.arn
}

output "job_definition_name" {
  description = "Name of the EC2 job definition."
  value       = aws_batch_job_definition.ec2.name
}

output "job_role_arn" {
  description = "ARN of the IAM role assumed by the EC2 job task."
  value       = var.job_role_arn
}
