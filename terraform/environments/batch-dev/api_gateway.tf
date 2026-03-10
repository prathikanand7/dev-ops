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

