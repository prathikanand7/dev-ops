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
    condition     = (length(split("operationId: \"cors", aws_api_gateway_rest_api.api.body)) - 1) == 5
    error_message = "Expected 5 CORS OPTIONS operations in openapi body: jobs, history_list, job_id, job_logs, job_results."
  }
}

run "all_options_integrations_are_mock_type" {
  command = plan

  assert {
    condition     = (length(split("type: \"MOCK\"", aws_api_gateway_rest_api.api.body)) - 1) == 5
    error_message = "All OPTIONS integrations in openapi body must be MOCK, Lambda must never be invoked for preflight."
  }
}

run "cors_response_headers_are_set_on_all_routes" {
  command = plan

  assert {
    condition = alltrue([
      (length(split("method.response.header.Access-Control-Allow-Origin", aws_api_gateway_rest_api.api.body)) - 1) == 5,
      (length(split("method.response.header.Access-Control-Allow-Methods", aws_api_gateway_rest_api.api.body)) - 1) == 5,
      (length(split("method.response.header.Access-Control-Allow-Headers", aws_api_gateway_rest_api.api.body)) - 1) == 5,
    ])
    error_message = "All 5 OPTIONS responses must set Origin, Methods, and Headers response parameters."
  }
}

run "cors_allow_headers_includes_x_api_key" {
  command = plan

  assert {
    condition = (length(split("Content-Type,x-api-key,Authorization", aws_api_gateway_rest_api.api.body)) - 1) >= 5
    error_message = "CORS Allow-Headers must include x-api-key, required by browser preflight for API key auth."
  }
}

# ── Lambda integrations ───────────────────────────────────────────────────────

run "all_lambda_integrations_are_aws_proxy" {
  command = plan

  assert {
    condition     = (length(split("type: \"AWS_PROXY\"", aws_api_gateway_rest_api.api.body)) - 1) == 5
    error_message = "All 5 functional Lambda integrations must be AWS_PROXY type."
  }
}

run "all_lambda_integrations_use_post_method" {
  command = plan

  # API Gateway always invokes Lambda via POST regardless of the client-facing HTTP method.
  assert {
    condition     = (length(split("httpMethod: \"POST\"", aws_api_gateway_rest_api.api.body)) - 1) == 5
    error_message = "All Lambda integrations in openapi body must use POST as the integration HTTP method."
  }
}

# ── API key requirement ───────────────────────────────────────────────────────

run "all_non_options_methods_require_api_key" {
  command = plan

  assert {
    condition     = (length(split("- ApiKeyAuth: []", aws_api_gateway_rest_api.api.body)) - 1) == 5
    error_message = "All 5 non-OPTIONS operations must require ApiKeyAuth."
  }
}

run "options_methods_do_not_require_api_key" {
  command = plan

  assert {
    condition     = (length(split("security: []", aws_api_gateway_rest_api.api.body)) - 1) == 5
    error_message = "All OPTIONS operations must use security: [] to avoid API key requirements for browser preflight."
  }
}

run "gateway_level_cors_responses_exist" {
  command = plan

  assert {
    condition = alltrue([
      aws_api_gateway_gateway_response.cors_4xx.response_type == "DEFAULT_4XX",
      aws_api_gateway_gateway_response.cors_5xx.response_type == "DEFAULT_5XX",
      aws_api_gateway_gateway_response.cors_missing_authentication_token.response_type == "MISSING_AUTHENTICATION_TOKEN",
      aws_api_gateway_gateway_response.cors_resource_not_found.response_type == "RESOURCE_NOT_FOUND",
    ])
    error_message = "Expected gateway-level CORS responses for DEFAULT_4XX, DEFAULT_5XX, MISSING_AUTHENTICATION_TOKEN, and RESOURCE_NOT_FOUND."
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
