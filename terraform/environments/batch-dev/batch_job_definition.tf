resource "aws_batch_job_definition" "lifewatch_fargate_job_definition" {
  name = "lifewatch-fargate-job-definition"
  type = "container"

  platform_capabilities = ["FARGATE"]

  container_properties = jsonencode({
    image = "020858641931.dkr.ecr.eu-west-1.amazonaws.com/r-notebook-worker:latest"

    command = ["echo", "Hello world. I am running the job"]

    fargatePlatformConfiguration = {
      platformVersion = "LATEST"
    }

    networkConfiguration = {
      assignPublicIp = "ENABLED"
    }

    resourceRequirements = [
      { type = "VCPU", value = "1.0" },
      { type = "MEMORY", value = "2048" }
    ]

    ephemeralStorage = {
      sizeInGiB = 21
    }

    runtimePlatform = {
      cpuArchitecture       = "X86_64"
      operatingSystemFamily = "LINUX"
    }

    executionRoleArn = "arn:aws:iam::020858641931:role/BatchEcsTaskExecutionRole"
  })

  tags = {
    Name = "lifewatch-fargate-job-definition"
  }
}