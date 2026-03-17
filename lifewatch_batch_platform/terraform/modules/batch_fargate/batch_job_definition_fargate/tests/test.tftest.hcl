# tests/job_definition_fargate.tftest.hcl

run "fargate_job_definition" {
  command = plan

  variables {
    project_name           = "test"
    profile_name           = "dev"
    container_image        = "nginx"
    container_command      = ["run"]
    vcpus                  = 2
    memory_mib             = 4096
    ephemeral_storage_gib  = 50
    execution_role_arn     = "arn:aws:iam::123456789012:role/execution"
    job_role_arn           = "arn:aws:iam::123456789012:role/job"
    s3_bucket_arn     = "arn:aws:s3:::dummy-bucket"

    tags = {
      Env = "test"
    }
  }

  assert {
    condition = contains(
      aws_batch_job_definition.fargate.platform_capabilities,
      "FARGATE"
    )
    error_message = "Must support FARGATE"
  }

  # Validate resourceRequirements mapping
  assert {
    condition = contains(
      [for r in jsondecode(aws_batch_job_definition.fargate.container_properties).resourceRequirements : r.value],
      "2"
    )
    error_message = "VCPU not correctly mapped"
  }

  assert {
    condition = contains(
      [for r in jsondecode(aws_batch_job_definition.fargate.container_properties).resourceRequirements : r.value],
      "4096"
    )
    error_message = "Memory not correctly mapped"
  }

  # Validate ephemeral storage
  assert {
    condition = jsondecode(
      aws_batch_job_definition.fargate.container_properties
    ).ephemeralStorage.sizeInGiB == 50
    error_message = "Ephemeral storage not wired correctly"
  }

  # Validate execution role exists
  assert {
    condition = jsondecode(
      aws_batch_job_definition.fargate.container_properties
    ).executionRoleArn != ""
    error_message = "Execution role must be set"
  }
}