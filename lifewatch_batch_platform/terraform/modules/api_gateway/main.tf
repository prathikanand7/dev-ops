################################
# REST API — driven by OpenAPI spec
################################

resource "aws_api_gateway_rest_api" "api" {
  name               = "${var.project_name}-api"
  binary_media_types = ["multipart/form-data", "*/*"]
  put_rest_api_mode  = "overwrite"

  body = templatefile("${path.module}/openapi.yaml", {
    batch_trigger_lambda_arn    = var.batch_trigger_lambda_arn
    job_history_list_lambda_arn = var.job_history_list_lambda_arn
    job_status_lambda_arn       = var.job_status_lambda_arn
    job_logs_lambda_arn         = var.job_logs_lambda_arn
    job_results_lambda_arn      = var.job_results_lambda_arn
  })
}

################################
# CORS — gateway-level error responses
#
# The OPTIONS preflight MOCK integrations are defined in openapi.yaml and
# imported as part of the API body above.
#
# These gateway responses add Access-Control-Allow-Origin to API Gateway's
# own error responses (e.g. 403 Missing Authentication Token, 429 Throttled)
# so the browser can read the error body instead of seeing an opaque CORS failure.
################################

locals {
  # TODO: restrict to specific origin(s) for production.
  cors_allow_origin = "'*'"
}

resource "aws_api_gateway_gateway_response" "cors_4xx" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  response_type = "DEFAULT_4XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = local.cors_allow_origin
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'OPTIONS,GET,POST'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,x-api-key,Authorization'"
  }

  response_templates = {
    "application/json" = "{\"message\": $context.error.messageString}"
  }
}

resource "aws_api_gateway_gateway_response" "cors_5xx" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  response_type = "DEFAULT_5XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = local.cors_allow_origin
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'OPTIONS,GET,POST'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,x-api-key,Authorization'"
  }

  response_templates = {
    "application/json" = "{\"message\": $context.error.messageString}"
  }
}

resource "aws_api_gateway_gateway_response" "cors_missing_authentication_token" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  response_type = "MISSING_AUTHENTICATION_TOKEN"
  status_code   = "403"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = local.cors_allow_origin
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'OPTIONS,GET,POST'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,x-api-key,Authorization'"
  }

  response_templates = {
    "application/json" = "{\"message\": $context.error.messageString}"
  }
}

resource "aws_api_gateway_gateway_response" "cors_resource_not_found" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  response_type = "RESOURCE_NOT_FOUND"
  status_code   = "404"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = local.cors_allow_origin
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'OPTIONS,GET,POST'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,x-api-key,Authorization'"
  }

  response_templates = {
    "application/json" = "{\"message\": $context.error.messageString}"
  }
}

################################
# Deployment
################################

resource "aws_api_gateway_deployment" "deployment" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = sha1(templatefile("${path.module}/openapi.yaml", {
      batch_trigger_lambda_arn    = var.batch_trigger_lambda_arn
      job_history_list_lambda_arn = var.job_history_list_lambda_arn
      job_status_lambda_arn       = var.job_status_lambda_arn
      job_logs_lambda_arn         = var.job_logs_lambda_arn
      job_results_lambda_arn      = var.job_results_lambda_arn
    }))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_rest_api.api,
    aws_api_gateway_gateway_response.cors_4xx,
    aws_api_gateway_gateway_response.cors_5xx,
    aws_api_gateway_gateway_response.cors_missing_authentication_token,
    aws_api_gateway_gateway_response.cors_resource_not_found,
  ]
}

################################
# Stage
################################

resource "aws_api_gateway_stage" "stage" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  deployment_id = aws_api_gateway_deployment.deployment.id
  stage_name    = var.stage_name
}
