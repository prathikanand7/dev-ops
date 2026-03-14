################################
# EC2 Job Queue
################################

resource "aws_batch_job_queue" "ec2" {
  name     = "${var.project_name}-ec2-job-queue"
  state    = "ENABLED"
  priority = var.priority

  compute_environment_order {
    order               = 1
    compute_environment = var.compute_environment_arn
  }

  job_state_time_limit_action {
    state            = "RUNNABLE"
    action           = "CANCEL"
    max_time_seconds = var.runnable_timeout_seconds
    reason           = "MISCONFIGURATION:COMPUTE_ENVIRONMENT_MAX_RESOURCE"
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-ec2-job-queue"
  })
}
