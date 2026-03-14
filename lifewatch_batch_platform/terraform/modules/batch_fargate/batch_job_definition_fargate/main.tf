################################
# IAM - Job Role (S3 access)
################################

resource "aws_iam_role" "batch_job_role" {
  name = "${var.project_name}-batch-job-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "batch_job_s3" {
  name = "${var.project_name}-batch-job-s3"
  role = aws_iam_role.batch_job_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = [var.s3_bucket_arn]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = ["${var.s3_bucket_arn}/*"]
      }
    ]
  })
}

################################
# Fargate Job Definition
################################

resource "aws_batch_job_definition" "fargate" {
  name                  = "${var.project_name}-fargate-job-definition"
  type                  = "container"
  platform_capabilities = ["FARGATE"]

  container_properties = jsonencode({
    image   = var.container_image
    command = var.container_command

    fargatePlatformConfiguration = {
      platformVersion = "LATEST"
    }

    networkConfiguration = {
      assignPublicIp = "DISABLED"
    }

    # Lambda dynamically injects JOB_ID and S3_JOB_PREFIX at submission time.
    environment = []

    resourceRequirements = [
      { type = "VCPU",   value = tostring(var.vcpus) },
      { type = "MEMORY", value = tostring(var.memory_mib) }
    ]

    ephemeralStorage = {
      sizeInGiB = var.ephemeral_storage_gib
    }

    runtimePlatform = {
      cpuArchitecture      = "X86_64"
      operatingSystemFamily = "LINUX"
    }

    executionRoleArn = var.execution_role_arn
    jobRoleArn       = aws_iam_role.batch_job_role.arn
  })

  tags = merge(var.tags, {
    Name = "${var.project_name}-fargate-job-definition"
  })
}
