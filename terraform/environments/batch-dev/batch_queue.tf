resource "aws_batch_job_queue" "lifewatch_fargate_job_queue" {
  name     = "lifewatch-fargate-job-queue"
  state    = "ENABLED"
  priority = 10

  compute_environment_order {
    order               = 1
    compute_environment = aws_batch_compute_environment.lifewatch_fargate_environment.arn
  }

  job_state_time_limit_action {
    state            = "RUNNABLE"
    action           = "CANCEL"
    max_time_seconds = 600
    reason           = "MISCONFIGURATION:COMPUTE_ENVIRONMENT_MAX_RESOURCE"
  }

  tags = {
    Name = "lifewatch-fargate-job-queue"
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
