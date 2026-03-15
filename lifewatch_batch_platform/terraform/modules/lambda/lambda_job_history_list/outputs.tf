output "function_name" {
  description = "Name of the job history list Lambda function."
  value       = aws_lambda_function.job_history_list.function_name
}

output "function_arn" {
  description = "ARN of the job history list Lambda function."
  value       = aws_lambda_function.job_history_list.arn
}

output "invoke_arn" {
  description = "Invoke ARN used by API Gateway to call this function."
  value       = aws_lambda_function.job_history_list.invoke_arn
}
