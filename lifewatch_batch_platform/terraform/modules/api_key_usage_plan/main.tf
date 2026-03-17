################################
# API Key
################################

resource "aws_api_gateway_api_key" "this" {
  name = var.lifewatch_key_name
}

################################
# Usage Plan
################################

resource "aws_api_gateway_usage_plan" "this" {
  name        = var.usage_plan_name
  description = var.usage_plan_description

  api_stages {
    api_id = var.api_id
    stage  = var.stage_name
  }

  throttle_settings {
    burst_limit = var.burst_limit
    rate_limit  = var.rate_limit
  }
}

################################
# Attach key to plan
################################

resource "aws_api_gateway_usage_plan_key" "this" {
  key_id        = aws_api_gateway_api_key.this.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.this.id
}
