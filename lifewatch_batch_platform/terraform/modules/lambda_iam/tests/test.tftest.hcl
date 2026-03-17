run "lambda_iam" {
  command = plan

  variables {
    project_name  = "test"
    s3_bucket_arn = "arn:aws:s3:::my-bucket"

    tags = {
      Env = "test"
    }
  }

  # Trust policy
  assert {
    condition = jsondecode(
      aws_iam_role.lambda.assume_role_policy
    ).Statement[0].Principal.Service == "lambda.amazonaws.com"
    error_message = "Lambda must be assumable by Lambda service"
  }

  # S3 access wiring (critical)
  assert {
    condition = contains(
      jsondecode(aws_iam_role_policy.lambda.policy).Statement[0].Resource,
      "arn:aws:s3:::my-bucket"
    )
    error_message = "S3 bucket ARN missing"
  }

  assert {
    condition = contains(
      jsondecode(aws_iam_role_policy.lambda.policy).Statement[0].Resource,
      "arn:aws:s3:::my-bucket/*"
    )
    error_message = "S3 object ARN missing"
  }

  # Batch permissions
  assert {
    condition = contains(
      jsondecode(aws_iam_role_policy.lambda.policy).Statement[1].Action,
      "batch:SubmitJob"
    )
    error_message = "Missing Batch SubmitJob permission"
  }
}