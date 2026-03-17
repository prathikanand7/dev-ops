run "validate_batch_compute_environment" {
  command = plan

  variables {
    project_name           = "test-project"
    profile_name           = "dev"
    service_role_arn       = "arn:aws:iam::123456789012:role/AWSBatchServiceRole"
    instance_profile_arn   = "arn:aws:iam::123456789012:instance-profile/ecsInstanceRole"
    allocation_strategy    = "BEST_FIT_PROGRESSIVE"
    max_vcpus              = 16
    instance_types         = ["t3.medium"]
    subnet_ids             = ["subnet-12345678"]
    security_group_ids     = ["sg-12345678"]

    ebs_iops               = 3000
    ebs_throughput         = 125
    ebs_volume_size_gb     = 50

    tags = {
      Environment = "test"
    }
  }

  assert {
    condition     = aws_batch_compute_environment.ec2.type == "MANAGED"
    error_message = "Compute environment should be MANAGED"
  }

  assert {
    condition     = aws_batch_compute_environment.ec2.compute_resources[0].type == "EC2"
    error_message = "Compute resources type should be EC2"
  }

  assert {
    condition     = aws_batch_compute_environment.ec2.compute_resources[0].max_vcpus == 16
    error_message = "Max vCPUs should match input"
  }

  assert {
    condition     = aws_launch_template.batch_ec2.block_device_mappings[0].ebs[0].volume_type == "gp3"
    error_message = "EBS volume type should be gp3"
  }

  assert {
    condition     = aws_launch_template.batch_ec2.metadata_options[0].http_tokens == "required"
    error_message = "IMDSv2 should be enforced"
  }
}