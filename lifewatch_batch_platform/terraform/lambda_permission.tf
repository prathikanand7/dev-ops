resource "aws_lambda_permission" "apigw_trigger_batch" {
  statement_id  = "AllowAPIGatewayInvokeBatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.batch_trigger.function_name
  principal     = "apigateway.amazonaws.com"
}

resource "aws_lambda_permission" "apigw_trigger_status" {
  statement_id  = "AllowAPIGatewayInvokeStatus"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.job_status.function_name
  principal     = "apigateway.amazonaws.com"
}

resource "aws_lambda_permission" "apigw_trigger_logs" {
  statement_id  = "AllowAPIGatewayInvokeLogs"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.job_logs.function_name
  principal     = "apigateway.amazonaws.com"
}

resource "aws_lambda_permission" "allow_api_gateway_job_results" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.job_results.function_name
  principal     = "apigateway.amazonaws.com"
}