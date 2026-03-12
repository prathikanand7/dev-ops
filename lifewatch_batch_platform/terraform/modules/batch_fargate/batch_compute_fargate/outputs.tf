output "compute_environment_arn" {
  description = "ARN of the Fargate compute environment."
  value       = aws_batch_compute_environment.fargate.arn
}

output "compute_environment_name" {
  description = "Name of the Fargate compute environment."
  value       = aws_batch_compute_environment.fargate.name
}
