resource "aws_batch_job_definition" "lifewatch_ec2_200gb_job_definition" {
  name = "lifewatch-ec2-200gb-job-definition"
  type = "container"

  platform_capabilities = ["EC2"]

  container_properties = jsonencode({
    image = "020858641931.dkr.ecr.eu-west-1.amazonaws.com/r-notebook-worker:latest"

    command = ["python", "worker.py"]

    # Left empty because Lambda dynamically injects JOB_ID and S3_JOB_PREFIX
    environment = []

    vcpus  = 2
    memory = 16384

    # Gives the Python script permission to talk to S3
    jobRoleArn = aws_iam_role.batch_job_role.arn
  })

  tags = {
    Name = "lifewatch-ec2-200gb-job-definition"
  }
}

resource "aws_batch_job_queue" "lifewatch_ec2_200gb_job_queue" {
  name     = "lifewatch-ec2-200gb-job-queue"
  state    = "ENABLED"
  priority = 20

  compute_environment_order {
    order               = 1
    compute_environment = aws_batch_compute_environment.lifewatch_ec2_200gb_environment.arn
  }

  job_state_time_limit_action {
    state            = "RUNNABLE"
    action           = "CANCEL"
    max_time_seconds = 600
    reason           = "MISCONFIGURATION:COMPUTE_ENVIRONMENT_MAX_RESOURCE"
  }

  tags = {
    Name = "lifewatch-ec2-200gb-job-queue"
  }
}
