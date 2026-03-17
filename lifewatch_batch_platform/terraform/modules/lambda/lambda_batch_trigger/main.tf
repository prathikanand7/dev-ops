################################
# Lambda Function
################################

resource "aws_lambda_function" "batch_trigger" {
  function_name    = "${var.project_name}-batch-trigger"
  role             = var.lambda_role_arn
  handler          = "lambda_function.lambda_handler"
  runtime          = var.runtime
  filename         = var.filename
  source_code_hash = filebase64sha256(var.filename)

  environment {
    variables = {
      BUCKET              = var.s3_bucket_name
      JOB_PROFILES_CONFIG = var.job_profiles_config_json
    }
  }
}

################################
# API Gateway Permission
################################

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.batch_trigger.function_name
  principal     = "apigateway.amazonaws.com"
}
