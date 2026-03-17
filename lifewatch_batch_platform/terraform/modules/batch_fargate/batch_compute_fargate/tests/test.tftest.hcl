# tests/compute_env_fargate.tftest.hcl

run "fargate_compute_env" {
  command = plan

  variables {
    project_name       = "test"
    profile_name       = "dev"
    max_vcpus          = 32
    subnet_ids         = ["subnet-123"]
    security_group_ids = ["sg-123"]
    service_role_arn   = "arn:aws:iam::123456789012:role/AWSBatchServiceRole"

    tags = {
      Env = "test"
    }
  }

  assert {
    condition = aws_batch_compute_environment.fargate.compute_resources[0].type == "FARGATE"
    error_message = "Must be FARGATE compute environment"
  }

  assert {
    condition = aws_batch_compute_environment.fargate.compute_resources[0].max_vcpus == 32
    error_message = "max_vcpus not wired correctly"
  }

  assert {
    condition = length(aws_batch_compute_environment.fargate.compute_resources[0].subnets) > 0
    error_message = "Subnets must be provided"
  }
}