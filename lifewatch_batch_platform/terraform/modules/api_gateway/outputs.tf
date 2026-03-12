output "api_id" {
  description = "ID of the REST API."
  value       = aws_api_gateway_rest_api.api.id
}

output "stage_name" {
  description = "Name of the deployed API Gateway stage."
  value       = aws_api_gateway_stage.stage.stage_name
}

output "invoke_url" {
  description = "Base invoke URL of the deployed stage."
  value       = aws_api_gateway_stage.stage.invoke_url
}
