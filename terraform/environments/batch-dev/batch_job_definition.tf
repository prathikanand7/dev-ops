resource "aws_batch_job_definition" "lifewatch_fargate_job_definition" {
  name = "lifewatch-fargate-job-definition"
  type = "container"

  platform_capabilities = ["FARGATE"]

  container_properties = jsonencode({
    image = "020858641931.dkr.ecr.eu-west-1.amazonaws.com/r-notebook-worker:latest"

    command = ["python", "worker.py"]

    fargatePlatformConfiguration = {
      platformVersion = "LATEST"
    }

    networkConfiguration = {
      assignPublicIp = "ENABLED"
    }

    # Left empty because Lambda dynamically injects JOB_ID and S3_JOB_PREFIX
    environment = []

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

    # Pull the image from ECR and send logs to CloudWatch
    executionRoleArn = "arn:aws:iam::020858641931:role/BatchEcsTaskExecutionRole"
    
    # Gives the Python script permission to talk to S3
    jobRoleArn       = aws_iam_role.batch_job_role.arn
  })

  tags = {
    Name = "lifewatch-fargate-job-definition"
  }
}