output "job_queue_arn" {
  description = "ARN of the EC2 job queue."
  value       = aws_batch_job_queue.ec2.arn
}

output "job_queue_name" {
  description = "Name of the EC2 job queue."
  value       = aws_batch_job_queue.ec2.name
}
