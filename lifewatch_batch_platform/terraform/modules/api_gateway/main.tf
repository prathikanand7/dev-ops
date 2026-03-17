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

  depends_on = [aws_api_gateway_rest_api.api]
}

################################
# Stage
################################

resource "aws_api_gateway_stage" "stage" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  deployment_id = aws_api_gateway_deployment.deployment.id
  stage_name    = var.stage_name
}
