resource "aws_iam_role" "batch_service_role" {
  name = "lifewatch-batch-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "batch.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "batch_service_role_attachment" {
  role       = aws_iam_role.batch_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

resource "aws_iam_role" "batch_ec2_instance_role" {
  name = "lifewatch-batch-ec2-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "batch_ec2_instance_role_ecs" {
  role       = aws_iam_role.batch_ec2_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_role_policy_attachment" "batch_ec2_instance_role_ecr_readonly" {
  role       = aws_iam_role.batch_ec2_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_instance_profile" "batch_ec2_instance_profile" {
  name = "lifewatch-batch-ec2-instance-profile"
  role = aws_iam_role.batch_ec2_instance_role.name
}

resource "aws_launch_template" "lifewatch_batch_ec2_200gb" {
  name_prefix            = "lifewatch-batch-ec2-200gb-"
  update_default_version = true

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      delete_on_termination = true
      encrypted             = true
      iops                  = 3000
      throughput            = 125
      volume_size           = 200
      volume_type           = "gp3"
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_put_response_hop_limit = 2
    http_tokens                 = "required"
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "lifewatch-batch-ec2-200gb"
    }
  }
}

resource "aws_batch_compute_environment" "lifewatch_fargate_environment" {
  name  = "lifewatch-fargate-environment"
  type  = "MANAGED"
  state = "ENABLED"

  compute_resources {
    type = "FARGATE"

    subnets = [
      aws_subnet.my_app_vpc_public_eu_west_1a.id,
      aws_subnet.my_app_vpc_public_eu_west_1b.id
    ]

    security_group_ids = [
      aws_security_group.batch_security_group.id
    ]

    max_vcpus = 256
  }

  depends_on = [
    aws_vpc_endpoint.s3,
    aws_vpc_endpoint.ecr_dkr,
    aws_vpc_endpoint.ecr_api,
    aws_vpc_endpoint.logs
  ]

  tags = {
    Name = "lifewatch-fargate-environment"
  }
}

resource "aws_batch_compute_environment" "lifewatch_ec2_200gb_environment" {
  name         = "lifewatch-ec2-200gb-environment"
  type         = "MANAGED"
  state        = "ENABLED"
  service_role = aws_iam_role.batch_service_role.arn

  compute_resources {
    type                = "EC2"
    allocation_strategy = "BEST_FIT_PROGRESSIVE"
    desired_vcpus       = 0
    max_vcpus           = 256
    min_vcpus           = 0

    instance_role = aws_iam_instance_profile.batch_ec2_instance_profile.arn
    instance_type = ["m6i.2xlarge", "m6i.4xlarge", "m5.2xlarge", "m5.4xlarge"]

    subnets = [
      aws_subnet.my_app_vpc_public_eu_west_1a.id,
      aws_subnet.my_app_vpc_public_eu_west_1b.id
    ]

    security_group_ids = [
      aws_security_group.batch_security_group.id
    ]

    ec2_configuration {
      image_type = "ECS_AL2"
    }

    launch_template {
      launch_template_id = aws_launch_template.lifewatch_batch_ec2_200gb.id
      version            = "$Latest"
    }

    tags = {
      Name = "lifewatch-ec2-200gb-batch"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.batch_service_role_attachment,
    aws_iam_role_policy_attachment.batch_ec2_instance_role_ecs,
    aws_iam_role_policy_attachment.batch_ec2_instance_role_ecr_readonly,
    aws_vpc_endpoint.s3,
    aws_vpc_endpoint.ecr_dkr,
    aws_vpc_endpoint.ecr_api,
    aws_vpc_endpoint.logs,
    aws_vpc_endpoint.ecs,
    aws_vpc_endpoint.ecs_agent,
    aws_vpc_endpoint.ecs_telemetry
  ]

  tags = {
    Name = "lifewatch-ec2-200gb-environment"
  }

  lifecycle {
    # Batch auto-scales desired vCPUs while jobs are queued/running.
    ignore_changes = [compute_resources[0].desired_vcpus]
  }
}
