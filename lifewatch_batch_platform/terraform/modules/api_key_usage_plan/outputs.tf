output "api_key_value" {
  description = "The API key value. Sensitive — use terraform output -raw api_key to retrieve it."
  value       = aws_api_gateway_api_key.this.value
  sensitive   = true
}

output "api_key_id" {
  description = "ID of the API key resource."
  value       = aws_api_gateway_api_key.this.id
}

output "usage_plan_id" {
  description = "ID of the usage plan."
  value       = aws_api_gateway_usage_plan.this.id
}
