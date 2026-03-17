run "s3_batch_payloads" {
  command = plan

  variables {
    project_name = "test"

    tags = {
      Env = "test"
    }
  }

  # Bucket naming includes account ID
  assert {
    condition = can(regex(
      "^test-batch-payloads-",
      aws_s3_bucket.batch_payloads.bucket
    ))
    error_message = "Bucket name must include project prefix"
  }

  # Tag check
  assert {
    condition = aws_s3_bucket.batch_payloads.tags["Name"] == "test-batch-payloads"
    error_message = "Name tag incorrect"
  }
}