################################
# REST API
################################

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.34"
    }
  }
}


resource "aws_api_gateway_rest_api" "api" {
  name               = "${var.project_name}-api"
  binary_media_types = ["multipart/form-data", "*/*"]
}

################################
# /batch
################################

resource "aws_api_gateway_resource" "batch" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "batch"
}

################################
# /batch/jobs
################################

resource "aws_api_gateway_resource" "jobs" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.batch.id
  path_part   = "jobs"
}

################################
# POST /batch/jobs
################################

resource "aws_api_gateway_method" "post_jobs" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.jobs.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "post_jobs_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.jobs.id
  http_method             = aws_api_gateway_method.post_jobs.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.batch_trigger_lambda_arn
}

################################
# /batch/jobs/history_list
################################

resource "aws_api_gateway_resource" "history_list" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.jobs.id
  path_part   = "history_list"
}

################################
# GET /batch/jobs/history_list
################################

resource "aws_api_gateway_method" "get_history_list" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.history_list.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "get_history_list_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.history_list.id
  http_method             = aws_api_gateway_method.get_history_list.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.job_history_list_lambda_arn
}

################################
# /batch/jobs/{job_id}
################################

resource "aws_api_gateway_resource" "job_id" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.jobs.id
  path_part   = "{job_id}"
}

################################
# GET /batch/jobs/{job_id}
################################

resource "aws_api_gateway_method" "get_job_status" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.job_id.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "job_status_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.job_id.id
  http_method             = aws_api_gateway_method.get_job_status.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.job_status_lambda_arn
}

################################
# /batch/jobs/{job_id}/logs
################################

resource "aws_api_gateway_resource" "job_logs" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.job_id.id
  path_part   = "logs"
}

resource "aws_api_gateway_method" "get_logs" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.job_logs.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "logs_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.job_logs.id
  http_method             = aws_api_gateway_method.get_logs.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.job_logs_lambda_arn
}

################################
# /batch/jobs/{job_id}/results
################################

resource "aws_api_gateway_resource" "job_results" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.job_id.id
  path_part   = "results"
}

resource "aws_api_gateway_method" "get_job_results" {
  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = aws_api_gateway_resource.job_results.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "job_results_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.job_results.id
  http_method             = aws_api_gateway_method.get_job_results.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.job_results_lambda_arn
}

################################
# CORS — shared settings
################################

locals {
  # TODO: Currently allows all origins. Should be restricted for production.
  cors_allow_origin = "*"
  # Headers required by browser preflight for API key + multipart requests.
  cors_allow_headers = "Content-Type,x-api-key,Authorization"

  # Route-specific CORS mapping used by the for_each resources below.
  cors_routes = {
    # POST /batch/jobs
    jobs = {
      resource_id   = aws_api_gateway_resource.jobs.id
      allow_methods = "OPTIONS,POST"
    }
    # GET /batch/jobs/history_list
    history_list = {
      resource_id   = aws_api_gateway_resource.history_list.id
      allow_methods = "OPTIONS,GET"
    }
    # GET /batch/jobs/{job_id}
    job_id = {
      resource_id   = aws_api_gateway_resource.job_id.id
      allow_methods = "OPTIONS,GET"
    }
    # GET /batch/jobs/{job_id}/logs
    job_logs = {
      resource_id   = aws_api_gateway_resource.job_logs.id
      allow_methods = "OPTIONS,GET"
    }
    # GET /batch/jobs/{job_id}/results
    job_results = {
      resource_id   = aws_api_gateway_resource.job_results.id
      allow_methods = "OPTIONS,GET"
    }
  }
}

# CORS: OPTIONS methods for all frontend-facing routes
resource "aws_api_gateway_method" "options" {
  for_each = local.cors_routes

  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = each.value.resource_id
  http_method   = "OPTIONS"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_integration" "options" {
  # MOCK integration: API Gateway answers preflight without invoking Lambda.
  for_each = local.cors_routes

  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = each.value.resource_id
  http_method      = aws_api_gateway_method.options[each.key].http_method
  type             = "MOCK"
  content_handling = "CONVERT_TO_TEXT"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options" {
  for_each = local.cors_routes

  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = each.value.resource_id
  http_method = aws_api_gateway_method.options[each.key].http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Headers" = true
  }
}

resource "aws_api_gateway_integration_response" "options" {
  for_each = local.cors_routes

  rest_api_id      = aws_api_gateway_rest_api.api.id
  resource_id      = each.value.resource_id
  http_method      = aws_api_gateway_method.options[each.key].http_method
  status_code      = aws_api_gateway_method_response.options[each.key].status_code
  content_handling = "CONVERT_TO_TEXT"

  response_templates = {
    "application/json" = ""
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'${local.cors_allow_origin}'"
    "method.response.header.Access-Control-Allow-Methods" = "'${each.value.allow_methods}'"
    "method.response.header.Access-Control-Allow-Headers" = "'${local.cors_allow_headers}'"
  }
}

################################
# Deployment
################################

resource "aws_api_gateway_deployment" "deployment" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  # Force redeployment whenever any integration or response changes.
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_rest_api.api.binary_media_types,
      aws_api_gateway_integration.post_jobs_lambda.id,
      aws_api_gateway_integration.get_history_list_lambda.id,
      aws_api_gateway_integration.job_status_lambda.id,
      aws_api_gateway_integration.logs_lambda.id,
      aws_api_gateway_integration.job_results_lambda.id,
      [for integration in values(aws_api_gateway_integration.options) : {
        id                = integration.id
        content_handling  = integration.content_handling
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
    aws_api_gateway_integration.get_history_list_lambda,
    aws_api_gateway_integration.job_status_lambda,
    aws_api_gateway_integration.logs_lambda,
    aws_api_gateway_integration.job_results_lambda,
    aws_api_gateway_integration.options
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