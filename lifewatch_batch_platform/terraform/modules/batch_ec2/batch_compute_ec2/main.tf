################################
# Launch Template
################################

resource "aws_launch_template" "batch_ec2" {
  name_prefix            = "${var.project_name}-${var.profile_name}-batch-ec2-"
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
      Name = "${var.project_name}-${var.profile_name}-batch-ec2"
    })
  }
}

################################
# EC2 Compute Environment
################################

resource "aws_batch_compute_environment" "ec2" {
  name         = "${var.project_name}-${var.profile_name}-environment"
  type         = "MANAGED"
  state        = "ENABLED"
  service_role = var.service_role_arn

  compute_resources {
    type                = "EC2"
    allocation_strategy = var.allocation_strategy
    desired_vcpus       = 0
    min_vcpus           = 0
    max_vcpus           = var.max_vcpus
    instance_role       = var.instance_profile_arn
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
      Name = "${var.project_name}-${var.profile_name}-batch"
    })
  }
  lifecycle {
    ignore_changes = [compute_resources[0].desired_vcpus]
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.profile_name}-environment"
  })
}
