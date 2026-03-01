resource "aws_batch_job_definition" "lifewatch_fargate_job_definition" {
  name = "lifewatch-fargate-job-definition"
  type = "container"

  platform_capabilities = ["FARGATE"]

  container_properties = jsonencode({
    image = "020858641931.dkr.ecr.eu-west-1.amazonaws.com/batch-hello-world:latest"

    command = ["python", "app.py"]

    fargatePlatformConfiguration = {
      platformVersion = "LATEST"
    }

    networkConfiguration = {
      assignPublicIp = "ENABLED"
    }

    # tells the job to use this s3 bucket as an environment variable, the lambda will override the KEY variable at submission time
    environment = [
      { name = "BUCKET", value = aws_s3_bucket.batch_payloads.bucket }
      # KEY will be overridden at submission time
    ]

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
    jobRoleArn       = aws_iam_role.batch_job_role.arn
  })

  tags = {
    Name = "lifewatch-fargate-job-definition"
  }
}