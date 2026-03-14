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
      BUCKET                  = var.s3_bucket_name
      STANDARD_JOB_QUEUE      = var.standard_job_queue_name
      STANDARD_JOB_DEFINITION = var.standard_job_definition_name
      EC2_200GB_JOB_QUEUE     = var.ec2_job_queue_name
      EC2_200GB_JOB_DEFINITION = var.ec2_job_definition_name
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
