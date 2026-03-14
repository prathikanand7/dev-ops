output "job_queue_arn" {
  description = "ARN of the Fargate job queue."
  value       = aws_batch_job_queue.fargate.arn
}

output "job_queue_name" {
  description = "Name of the Fargate job queue."
  value       = aws_batch_job_queue.fargate.name
}
