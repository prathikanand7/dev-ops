output "role_arn" {
  description = "ARN of the shared Lambda IAM role."
  value       = aws_iam_role.lambda.arn
}

output "role_name" {
  description = "Name of the shared Lambda IAM role."
  value       = aws_iam_role.lambda.name
}
