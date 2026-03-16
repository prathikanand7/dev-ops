output "batch_service_role_arn" {
  description = "ARN of the Batch service role."
  value       = aws_iam_role.batch_service_role.arn
}

output "ec2_instance_profile_arn" {
  description = "ARN of the EC2 instance profile for Batch compute environments."
  value       = aws_iam_instance_profile.ec2_instance_profile.arn
}

output "batch_job_role_arn" {
  description = "ARN of the job execution role providing access to S3 payloads."
  value       = aws_iam_role.batch_job_role.arn
}
