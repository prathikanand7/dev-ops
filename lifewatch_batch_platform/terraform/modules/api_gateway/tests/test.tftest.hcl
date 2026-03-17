# modules/api_gateway/tests/api_gateway_unit.tftest.hcl

mock_provider "aws" {}

variables {
  project_name = "test-project"
  stage_name   = "test"

  batch_trigger_lambda_arn    = "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-1:123456789012:function:stub-batch/invocations"
  job_status_lambda_arn       = "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-1:123456789012:function:stub-status/invocations"
  job_logs_lambda_arn         = "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-1:123456789012:function:stub-logs/invocations"
  job_results_lambda_arn      = "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-1:123456789012:function:stub-results/invocations"
  job_history_list_lambda_arn = "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-1:123456789012:function:stub-history/invocations"
}

# ── Naming ────────────────────────────────────────────────────────────────────

run "api_is_named_correctly" {
  command = plan

  assert {
    condition     = aws_api_gateway_rest_api.api.name == "test-project-api"
    error_message = "REST API name must follow the <project_name>-api convention."
  }
}

run "stage_name_passed_through_correctly" {
  command = plan

  assert {
    condition     = aws_api_gateway_stage.stage.stage_name == "test"
    error_message = "Stage name does not match the input variable."
  }
}

# ── CORS coverage ─────────────────────────────────────────────────────────────

run "all_five_cors_routes_have_options_method" {
  command = plan

  assert {
    condition     = length(aws_api_gateway_method.options) == 5
    error_message = "Expected OPTIONS methods for all 5 routes: jobs, history_list, job_id, job_logs, job_results."
  }
}

run "all_options_integrations_are_mock_type" {
  command = plan

  assert {
    condition = alltrue([
      for k, v in aws_api_gateway_integration.options : v.type == "MOCK"
    ])
    error_message = "All OPTIONS integrations must be MOCK — Lambda must never be invoked for preflight."
  }
}

run "cors_response_headers_are_set_on_all_routes" {
  command = plan

  assert {
    condition = alltrue([
      for k, v in aws_api_gateway_integration_response.options :
        lookup(v.response_parameters, "method.response.header.Access-Control-Allow-Origin", null) != null &&
        lookup(v.response_parameters, "method.response.header.Access-Control-Allow-Methods", null) != null &&
        lookup(v.response_parameters, "method.response.header.Access-Control-Allow-Headers", null) != null
    ])
    error_message = "All CORS integration responses must set Origin, Methods, and Headers response parameters."
  }
}

run "cors_allow_headers_includes_x_api_key" {
  command = plan

  assert {
    condition = alltrue([
      for k, v in aws_api_gateway_integration_response.options :
        can(regex("x-api-key", v.response_parameters["method.response.header.Access-Control-Allow-Headers"]))
    ])
    error_message = "CORS Allow-Headers must include x-api-key — required by browser preflight for API key auth."
  }
}

# ── Lambda integrations ───────────────────────────────────────────────────────

run "all_lambda_integrations_are_aws_proxy" {
  command = plan

  assert {
    condition = alltrue([
      aws_api_gateway_integration.post_jobs_lambda.type        == "AWS_PROXY",
      aws_api_gateway_integration.get_history_list_lambda.type == "AWS_PROXY",
      aws_api_gateway_integration.job_status_lambda.type       == "AWS_PROXY",
      aws_api_gateway_integration.logs_lambda.type             == "AWS_PROXY",
      aws_api_gateway_integration.job_results_lambda.type      == "AWS_PROXY",
    ])
    error_message = "All Lambda integrations must be AWS_PROXY type."
  }
}

run "all_lambda_integrations_use_post_method" {
  command = plan

  # API Gateway always invokes Lambda via POST regardless of the client-facing HTTP method.
  assert {
    condition = alltrue([
      aws_api_gateway_integration.post_jobs_lambda.integration_http_method        == "POST",
      aws_api_gateway_integration.get_history_list_lambda.integration_http_method == "POST",
      aws_api_gateway_integration.job_status_lambda.integration_http_method       == "POST",
      aws_api_gateway_integration.logs_lambda.integration_http_method             == "POST",
      aws_api_gateway_integration.job_results_lambda.integration_http_method      == "POST",
    ])
    error_message = "All Lambda integrations must use POST as the integration HTTP method."
  }
}

# ── API key requirement ───────────────────────────────────────────────────────

run "all_non_options_methods_require_api_key" {
  command = plan

  assert {
    condition = alltrue([
      aws_api_gateway_method.post_jobs.api_key_required,
      aws_api_gateway_method.get_history_list.api_key_required,
      aws_api_gateway_method.get_job_status.api_key_required,
      aws_api_gateway_method.get_logs.api_key_required,
      aws_api_gateway_method.get_job_results.api_key_required,
    ])
    error_message = "All non-OPTIONS methods must have api_key_required = true."
  }
}

run "options_methods_do_not_require_api_key" {
  command = plan

  assert {
    condition = alltrue([
      for k, v in aws_api_gateway_method.options : !coalesce(v.api_key_required, false)
    ])
    error_message = "OPTIONS methods must NOT require an API key — this breaks browser CORS preflight."
  }
}

# ── Binary media types ────────────────────────────────────────────────────────

run "api_supports_multipart_binary_media" {
  command = plan

  assert {
    condition = contains(
      aws_api_gateway_rest_api.api.binary_media_types,
      "multipart/form-data"
    )
    error_message = "REST API must declare multipart/form-data as a binary media type."
  }
}