output "compute_environment_arn" {
  description = "ARN of the EC2 compute environment."
  value       = aws_batch_compute_environment.ec2.arn
}

output "compute_environment_name" {
  description = "Name of the EC2 compute environment."
  value       = aws_batch_compute_environment.ec2.name
}

output "batch_service_role_arn" {
  description = "ARN of the Batch service IAM role."
  value       = var.service_role_arn
}

output "ec2_instance_profile_arn" {
  description = "ARN of the EC2 instance profile used by Batch."
  value       = var.instance_profile_arn
}

output "launch_template_id" {
  description = "ID of the launch template attached to the compute environment."
  value       = aws_launch_template.batch_ec2.id
}
