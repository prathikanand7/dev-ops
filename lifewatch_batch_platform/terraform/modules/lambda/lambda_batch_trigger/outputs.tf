output "function_name" {
  description = "Name of the batch trigger Lambda function."
  value       = aws_lambda_function.batch_trigger.function_name
}

output "function_arn" {
  description = "ARN of the batch trigger Lambda function."
  value       = aws_lambda_function.batch_trigger.arn
}

output "invoke_arn" {
  description = "Invoke ARN used by API Gateway to call this function."
  value       = aws_lambda_function.batch_trigger.invoke_arn
}
