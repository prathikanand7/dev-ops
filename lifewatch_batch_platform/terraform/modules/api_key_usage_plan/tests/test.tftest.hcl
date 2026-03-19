run "api_key_is_created_with_correct_name" {
  command = plan

  variables {
    lifewatch_key_name     = "test-api-key"
    api_id                 = "abc123def"
    stage_name             = "dev"
    usage_plan_name        = "test-usage-plan"
    usage_plan_description = "Test usage plan"
    burst_limit            = 5
    rate_limit             = 10
    quota_limit            = null
    quota_offset           = 0
    quota_period           = "WEEK"
  }

  assert {
    condition     = aws_api_gateway_api_key.this.name == "test-api-key"
    error_message = "API key name should match lifewatch_key_name variable."
  }
}

run "api_key_is_enabled_by_default" {
  command = plan

  variables {
    lifewatch_key_name     = "test-api-key"
    api_id                 = "abc123def"
    stage_name             = "dev"
    usage_plan_name        = "test-usage-plan"
    usage_plan_description = "Test usage plan"
    burst_limit            = 5
    rate_limit             = 10
    quota_limit            = null
    quota_offset           = 0
    quota_period           = "WEEK"
  }

  assert {
    condition     = aws_api_gateway_api_key.this.enabled == true
    error_message = "API key should be enabled by default."
  }
}

run "usage_plan_is_created_with_correct_name_and_description" {
  command = plan

  variables {
    lifewatch_key_name     = "test-api-key"
    api_id                 = "abc123def"
    stage_name             = "dev"
    usage_plan_name        = "test-usage-plan"
    usage_plan_description = "Test usage plan description"
    burst_limit            = 5
    rate_limit             = 10
    quota_limit            = null
    quota_offset           = 0
    quota_period           = "WEEK"
  }

  assert {
    condition     = aws_api_gateway_usage_plan.this.name == "test-usage-plan"
    error_message = "Usage plan name should match usage_plan_name variable."
  }

  assert {
    condition     = aws_api_gateway_usage_plan.this.description == "Test usage plan description"
    error_message = "Usage plan description should match usage_plan_description variable."
  }
}

run "throttle_settings_are_applied_correctly" {
  command = plan

  variables {
    lifewatch_key_name     = "test-api-key"
    api_id                 = "abc123def"
    stage_name             = "dev"
    usage_plan_name        = "test-usage-plan"
    usage_plan_description = "Test usage plan"
    burst_limit            = 5
    rate_limit             = 10
    quota_limit            = null
    quota_offset           = 0
    quota_period           = "WEEK"
  }

  assert {
    condition     = aws_api_gateway_usage_plan.this.throttle_settings[0].burst_limit == 5
    error_message = "Burst limit should match burst_limit variable."
  }

  assert {
    condition     = aws_api_gateway_usage_plan.this.throttle_settings[0].rate_limit == 10
    error_message = "Rate limit should match rate_limit variable."
  }
}

run "quota_is_not_created_when_quota_limit_is_null" {
  command = plan

  variables {
    lifewatch_key_name     = "test-api-key"
    api_id                 = "abc123def"
    stage_name             = "dev"
    usage_plan_name        = "test-usage-plan"
    usage_plan_description = "Test usage plan"
    burst_limit            = 5
    rate_limit             = 10
    quota_limit            = null
    quota_offset           = 0
    quota_period           = "WEEK"
  }

  assert {
    condition     = length(aws_api_gateway_usage_plan.this.quota_settings) == 0
    error_message = "Quota settings should not be created when quota_limit is null."
  }
}
