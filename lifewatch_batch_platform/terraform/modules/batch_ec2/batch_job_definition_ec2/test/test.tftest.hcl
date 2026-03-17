run "ec2_job_definition" {
  command = plan

  variables {
    project_name     = "test"
    profile_name     = "dev"
    container_image  = "nginx"
    container_command = ["echo", "hello"]
    vcpus            = 2
    memory_mib       = 1024
    job_role_arn     = "arn:aws:iam::123456789012:role/test-role"

    s3_bucket_arn     = "arn:aws:s3:::dummy-bucket"

    tags = {
      Env = "test"
    }
  }

  # Ensure correct platform
  assert {
    condition     = contains(aws_batch_job_definition.ec2.platform_capabilities, "EC2")
    error_message = "Job definition must support EC2"
  }

  # Ensure CPU/memory wired correctly (JSON decode)
  assert {
    condition = jsondecode(
      aws_batch_job_definition.ec2.container_properties
    ).vcpus == 2
    error_message = "vCPUs not wired correctly"
  }

  assert {
    condition = jsondecode(
      aws_batch_job_definition.ec2.container_properties
    ).memory == 1024
    error_message = "Memory not wired correctly"
  }

  # Ensure role is passed
  assert {
    condition = jsondecode(
      aws_batch_job_definition.ec2.container_properties
    ).jobRoleArn != ""
    error_message = "Job role must be set"
  }
}