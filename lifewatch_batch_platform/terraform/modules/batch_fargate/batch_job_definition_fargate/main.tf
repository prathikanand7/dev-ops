################################
# Fargate Job Definition
################################

resource "aws_batch_job_definition" "fargate" {
  name                  = "${var.project_name}-${var.profile_name}-job-definition"
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
      { type = "VCPU", value = tostring(var.vcpus) },
      { type = "MEMORY", value = tostring(var.memory_mib) }
    ]

    ephemeralStorage = {
      sizeInGiB = var.ephemeral_storage_gib
    }

    runtimePlatform = {
      cpuArchitecture       = "X86_64"
      operatingSystemFamily = "LINUX"
    }

    executionRoleArn = var.execution_role_arn
    jobRoleArn       = var.job_role_arn
  })

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.profile_name}-job-definition"
  })
}
