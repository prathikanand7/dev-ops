################################
# REST API
################################

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
# Deployment
################################

resource "aws_api_gateway_deployment" "deployment" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  depends_on = [
    aws_api_gateway_integration.post_jobs_lambda,
    aws_api_gateway_integration.job_status_lambda,
    aws_api_gateway_integration.logs_lambda,
    aws_api_gateway_integration.job_results_lambda
  ]
}

resource "aws_api_gateway_stage" "stage" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  deployment_id = aws_api_gateway_deployment.deployment.id
  stage_name    = var.stage_name
}