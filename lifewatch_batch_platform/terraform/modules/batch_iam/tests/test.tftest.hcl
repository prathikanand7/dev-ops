run "batch_iam_roles" {
  command = plan

  variables {
    project_name  = "test"
    s3_bucket_arn = "arn:aws:s3:::my-bucket"

    tags = {
      Env = "test"
    }
  }

  ################################
  # Batch Service Role
  ################################

  assert {
    condition = aws_iam_role.batch_service_role.name == "test-batch-service-role"
    error_message = "Batch service role name incorrect"
  }

  # Validate trust policy
  assert {
    condition = jsondecode(
      aws_iam_role.batch_service_role.assume_role_policy
    ).Statement[0].Principal.Service == "batch.amazonaws.com"
    error_message = "Batch service role trust policy incorrect"
  }

  ################################
  # EC2 Instance Role
  ################################

  assert {
    condition = jsondecode(
      aws_iam_role.ec2_instance_role.assume_role_policy
    ).Statement[0].Principal.Service == "ec2.amazonaws.com"
    error_message = "EC2 role must be assumable by EC2"
  }

  # Ensure instance profile is linked
  assert {
    condition = aws_iam_instance_profile.ec2_instance_profile.role == aws_iam_role.ec2_instance_role.name
    error_message = "Instance profile not linked to EC2 role"
  }

  ################################
  # Job Role
  ################################

  assert {
    condition = jsondecode(
      aws_iam_role.batch_job_role.assume_role_policy
    ).Statement[0].Principal.Service == "ecs-tasks.amazonaws.com"
    error_message = "Job role must be assumable by ECS tasks"
  }

  ################################
  # S3 Policy Wiring (HIGH VALUE)
  ################################

  # Check bucket-level permission
  assert {
    condition = contains(
      jsondecode(aws_iam_role_policy.batch_job_s3.policy).Statement[0].Resource,
      "arn:aws:s3:::my-bucket"
    )
    error_message = "S3 bucket ARN not correctly wired"
  }

  # Check object-level permission
  assert {
    condition = contains(
      jsondecode(aws_iam_role_policy.batch_job_s3.policy).Statement[1].Resource,
      "arn:aws:s3:::my-bucket/*"
    )
    error_message = "S3 object ARN not correctly wired"
  }

  ################################
  # Managed Policy Attachments
  ################################

  assert {
    condition = aws_iam_role_policy_attachment.ec2_instance_ecs.policy_arn == "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
    error_message = "Missing ECS policy attachment"
  }

  assert {
    condition = aws_iam_role_policy_attachment.ec2_instance_ecr_readonly.policy_arn == "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
    error_message = "Missing ECR read-only policy"
  }
}