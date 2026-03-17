output "function_name" {
  description = "Name of the job logs Lambda function."
  value       = aws_lambda_function.job_logs.function_name
}

output "function_arn" {
  description = "ARN of the job logs Lambda function."
  value       = aws_lambda_function.job_logs.arn
}

output "invoke_arn" {
  description = "Invoke ARN used by API Gateway to call this function."
  value       = aws_lambda_function.job_logs.invoke_arn
}
