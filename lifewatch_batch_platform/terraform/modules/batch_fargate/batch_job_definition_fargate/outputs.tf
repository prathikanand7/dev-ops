output "job_definition_arn" {
  description = "ARN of the Fargate job definition."
  value       = aws_batch_job_definition.fargate.arn
}

output "job_definition_name" {
  description = "Name of the Fargate job definition."
  value       = aws_batch_job_definition.fargate.name
}

output "job_role_arn" {
  description = "ARN of the IAM role assumed by the Fargate job task."
  value       = aws_iam_role.batch_job_role.arn
}
