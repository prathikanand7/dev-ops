################################
# EC2 Job Definition
################################

resource "aws_batch_job_definition" "ec2" {
  name                  = "${var.project_name}-${var.profile_name}-job-definition"
  type                  = "container"
  platform_capabilities = ["EC2"]

  container_properties = jsonencode({
    image   = var.container_image
    command = var.container_command

    # Lambda dynamically injects JOB_ID and S3_JOB_PREFIX at submission time.
    environment = []

    vcpus  = var.vcpus
    memory = var.memory_mib

    jobRoleArn = var.job_role_arn
  })

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.profile_name}-job-definition"
  })
}

