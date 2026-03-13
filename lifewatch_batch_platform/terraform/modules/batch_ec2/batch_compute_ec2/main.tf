################################
# IAM - Batch Service Role
################################

resource "aws_iam_role" "batch_service_role" {
  name = "${var.project_name}-batch-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "batch.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "batch_service_role" {
  role       = aws_iam_role.batch_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

################################
# IAM — EC2 Instance Role
################################

resource "aws_iam_role" "ec2_instance_role" {
  name = "${var.project_name}-batch-ec2-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ec2_instance_ecs" {
  role       = aws_iam_role.ec2_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_role_policy_attachment" "ec2_instance_ecr_readonly" {
  role       = aws_iam_role.ec2_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_instance_profile" "ec2_instance_profile" {
  name = "${var.project_name}-batch-ec2-instance-profile"
  role = aws_iam_role.ec2_instance_role.name
}

################################
# Launch Template
################################

resource "aws_launch_template" "batch_ec2" {
  name_prefix            = "${var.project_name}-batch-ec2-"
  update_default_version = true

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      delete_on_termination = true
      encrypted             = true
      iops                  = var.ebs_iops
      throughput            = var.ebs_throughput
      volume_size           = var.ebs_volume_size_gb
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
    tags = merge(var.tags, {
      Name = "${var.project_name}-batch-ec2"
    })
  }
}

################################
# EC2 Compute Environment
################################

resource "aws_batch_compute_environment" "ec2" {
  name         = "${var.project_name}-ec2-environment"
  type         = "MANAGED"
  state        = "ENABLED"
  service_role = aws_iam_role.batch_service_role.arn

  compute_resources {
    type                = "EC2"
    allocation_strategy = var.allocation_strategy
    desired_vcpus       = 0
    min_vcpus           = 0
    max_vcpus           = var.max_vcpus
    instance_role       = aws_iam_instance_profile.ec2_instance_profile.arn
    instance_type       = var.instance_types
    subnets             = var.subnet_ids
    security_group_ids  = var.security_group_ids

    ec2_configuration {
      image_type = "ECS_AL2"
    }

    launch_template {
      launch_template_id = aws_launch_template.batch_ec2.id
      version            = "$Latest"
    }

    tags = merge(var.tags, {
      Name = "${var.project_name}-ec2-batch"
    })
  }

  depends_on = [
    aws_iam_role_policy_attachment.batch_service_role,
    aws_iam_role_policy_attachment.ec2_instance_ecs,
    aws_iam_role_policy_attachment.ec2_instance_ecr_readonly,
  ]

  # Batch auto-scales desired_vcpus while jobs are running; ignore drift.
  lifecycle {
    ignore_changes = [compute_resources[0].desired_vcpus]
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-ec2-environment"
  })
}
