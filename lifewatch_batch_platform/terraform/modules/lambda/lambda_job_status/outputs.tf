output "function_name" {
  description = "Name of the job status Lambda function."
  value       = aws_lambda_function.job_status.function_name
}

output "function_arn" {
  description = "ARN of the job status Lambda function."
  value       = aws_lambda_function.job_status.arn
}

output "invoke_arn" {
  description = "Invoke ARN used by API Gateway to call this function."
  value       = aws_lambda_function.job_status.invoke_arn
}
