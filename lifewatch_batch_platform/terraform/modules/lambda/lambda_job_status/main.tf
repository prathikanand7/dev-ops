################################
# Lambda Function
################################

resource "aws_lambda_function" "job_status" {
  function_name    = "${var.project_name}-job-status"
  role             = var.lambda_role_arn
  handler          = "status.lambda_handler"
  runtime          = var.runtime
  filename         = var.filename
  source_code_hash = filebase64sha256(var.filename)
  timeout          = var.timeout

  environment {
    variables = {
      BUCKET = var.s3_bucket_name
    }
  }
}

################################
# API Gateway Permission
################################

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.job_status.function_name
  principal     = "apigateway.amazonaws.com"
}
