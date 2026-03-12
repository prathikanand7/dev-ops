output "function_name" {
  description = "Name of the job results Lambda function."
  value       = aws_lambda_function.job_results.function_name
}

output "function_arn" {
  description = "ARN of the job results Lambda function."
  value       = aws_lambda_function.job_results.arn
}

output "invoke_arn" {
  description = "Invoke ARN used by API Gateway to call this function."
  value       = aws_lambda_function.job_results.invoke_arn
}
