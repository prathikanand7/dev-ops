resource "aws_api_gateway_rest_api" "lifewatch_api" {
  name               = "lifewatch-api"
  binary_media_types = ["multipart/form-data", "*/*"]
}

# /batch resource
resource "aws_api_gateway_resource" "batch" {
  rest_api_id = aws_api_gateway_rest_api.lifewatch_api.id
  parent_id   = aws_api_gateway_rest_api.lifewatch_api.root_resource_id
  path_part   = "batch"
}

# /batch/jobs resource 
resource "aws_api_gateway_resource" "jobs" {
  rest_api_id = aws_api_gateway_rest_api.lifewatch_api.id
  parent_id   = aws_api_gateway_resource.batch.id
  path_part   = "jobs"
}

# POST /batch/jobs
resource "aws_api_gateway_method" "post_jobs" {
  rest_api_id      = aws_api_gateway_rest_api.lifewatch_api.id
  resource_id      = aws_api_gateway_resource.jobs.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "post_jobs_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.lifewatch_api.id
  resource_id             = aws_api_gateway_resource.jobs.id
  http_method             = aws_api_gateway_method.post_jobs.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.batch_trigger.invoke_arn
}

# /batch/jobs/{job_id}
resource "aws_api_gateway_resource" "job_id" {
  rest_api_id = aws_api_gateway_rest_api.lifewatch_api.id
  parent_id   = aws_api_gateway_resource.jobs.id
  path_part   = "{job_id}"
}

# batch/jobs/{job_id} GET method (status)
resource "aws_api_gateway_method" "get_job_status" {
  rest_api_id      = aws_api_gateway_rest_api.lifewatch_api.id
  resource_id      = aws_api_gateway_resource.job_id.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "job_status_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.lifewatch_api.id
  resource_id             = aws_api_gateway_resource.job_id.id
  http_method             = aws_api_gateway_method.get_job_status.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.job_status.invoke_arn
}

# batch/jobs/{job_id}/logs resource
resource "aws_api_gateway_resource" "job_logs" {
  rest_api_id = aws_api_gateway_rest_api.lifewatch_api.id
  parent_id   = aws_api_gateway_resource.job_id.id
  path_part   = "logs"
}

# batch/jobs/{job_id}/logs GET method
resource "aws_api_gateway_method" "get_logs" {
  rest_api_id      = aws_api_gateway_rest_api.lifewatch_api.id
  resource_id      = aws_api_gateway_resource.job_logs.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "logs_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.lifewatch_api.id
  resource_id             = aws_api_gateway_resource.job_logs.id
  http_method             = aws_api_gateway_method.get_logs.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.job_logs.invoke_arn
}

#  batch/jobs/{job_id}/results resource
resource "aws_api_gateway_resource" "job_results" {
  rest_api_id = aws_api_gateway_rest_api.lifewatch_api.id
  parent_id   = aws_api_gateway_resource.job_id.id
  path_part   = "results"
}

# GET method
resource "aws_api_gateway_method" "get_job_results" {
  rest_api_id      = aws_api_gateway_rest_api.lifewatch_api.id
  resource_id      = aws_api_gateway_resource.job_results.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

# Integration with Lambda
resource "aws_api_gateway_integration" "job_results_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.lifewatch_api.id
  resource_id             = aws_api_gateway_resource.job_results.id
  http_method             = aws_api_gateway_method.get_job_results.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.job_results.invoke_arn
}

# Shared CORS settings reused across all OPTIONS routes
locals {
  # TODO: Currently allows all origins. Should be modified for production
  cors_allow_origin  = "*"
  # Headers needed by browser preflight for API key + multipart requests.
  cors_allow_headers = "Content-Type,x-api-key,Authorization"

  # Route-specific CORS mapping used by the for_each resources below.
  cors_routes = {
    # POST /batch/jobs
    jobs = {
      resource_id    = aws_api_gateway_resource.jobs.id
      allow_methods  = "OPTIONS,POST"
    }
    # GET /batch/jobs/{job_id}
    job_id = {
      resource_id    = aws_api_gateway_resource.job_id.id
      allow_methods  = "OPTIONS,GET"
    }
    # GET /batch/jobs/{job_id}/logs
    job_logs = {
      resource_id    = aws_api_gateway_resource.job_logs.id
      allow_methods  = "OPTIONS,GET"
    }
    # GET /batch/jobs/{job_id}/results
    job_results = {
      resource_id    = aws_api_gateway_resource.job_results.id
      allow_methods  = "OPTIONS,GET"
    }
  }
}

# CORS: OPTIONS methods for all frontend-facing routes
resource "aws_api_gateway_method" "options" {
  # Creates one OPTIONS method per entry in local.cors_routes.
  for_each = local.cors_routes

  rest_api_id   = aws_api_gateway_rest_api.lifewatch_api.id
  resource_id   = each.value.resource_id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options" {
  # Uses MOCK integration so API Gateway can answer preflight without Lambda invocation.
  for_each = local.cors_routes

  rest_api_id = aws_api_gateway_rest_api.lifewatch_api.id
  resource_id = each.value.resource_id
  http_method = aws_api_gateway_method.options[each.key].http_method
  type        = "MOCK"
  content_handling = "CONVERT_TO_TEXT"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options" {
  # Declares which CORS headers are returned by the OPTIONS method.
  for_each = local.cors_routes

  rest_api_id = aws_api_gateway_rest_api.lifewatch_api.id
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
  # Injects concrete header values into the preflight response.
  for_each = local.cors_routes

  rest_api_id = aws_api_gateway_rest_api.lifewatch_api.id
  resource_id = each.value.resource_id
  http_method = aws_api_gateway_method.options[each.key].http_method
  status_code = aws_api_gateway_method_response.options[each.key].status_code
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

