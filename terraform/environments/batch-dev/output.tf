output "lifewatch_api_key" {
  value     = aws_api_gateway_api_key.lifewatch_key.value
  sensitive = true
}

output "api_gateway_url" {
  value = "https://${aws_api_gateway_rest_api.lifewatch_api.id}.execute-api.eu-west-1.amazonaws.com/dev"
}