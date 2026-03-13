resource "aws_api_gateway_api_key" "lifewatch_key" {
  name = "lifewatch-api-key"
}

resource "aws_api_gateway_deployment" "lifewatch" {
  rest_api_id = aws_api_gateway_rest_api.lifewatch_api.id

  # Force redeployment if dependencies change
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_rest_api.lifewatch_api.binary_media_types,
      aws_api_gateway_integration.post_jobs_lambda.id,
      aws_api_gateway_integration.job_status_lambda.id,
      aws_api_gateway_integration.logs_lambda.id,
      aws_api_gateway_integration.job_results_lambda.id,
      [for integration in values(aws_api_gateway_integration.options) : {
        id               = integration.id
        content_handling = integration.content_handling
        request_templates = integration.request_templates
      }],
      [for response in values(aws_api_gateway_integration_response.options) : {
        id                  = response.id
        content_handling    = response.content_handling
        response_parameters = response.response_parameters
        response_templates  = response.response_templates
      }],
      [for response in values(aws_api_gateway_method_response.options) : {
        id                  = response.id
        response_parameters = response.response_parameters
      }]
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.post_jobs_lambda,
    aws_api_gateway_integration.job_status_lambda,
    aws_api_gateway_integration.logs_lambda,
    aws_api_gateway_integration.job_results_lambda,
    aws_api_gateway_integration.options
  ]
}

resource "aws_api_gateway_stage" "lifewatch_stage" {
  deployment_id = aws_api_gateway_deployment.lifewatch.id
  rest_api_id   = aws_api_gateway_rest_api.lifewatch_api.id
  stage_name    = "dev"
}

resource "aws_api_gateway_usage_plan" "lifewatch_plan" {
  name        = "lifewatch-usage-plan"
  description = "Usage plan for Lifewatch REST API"

  api_stages {
    api_id = aws_api_gateway_rest_api.lifewatch_api.id
    stage  = aws_api_gateway_stage.lifewatch_stage.stage_name
  }


  throttle_settings {
    burst_limit = 5
    rate_limit  = 10
  }

  #   quota_settings {
  #     limit  = 20
  #     offset = 2
  #     period = "WEEK"
  #   }
}

resource "aws_api_gateway_usage_plan_key" "main" {
  key_id        = aws_api_gateway_api_key.lifewatch_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.lifewatch_plan.id
}