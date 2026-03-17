run "ec2_job_queue" {
  command = plan

  variables {
    project_name                = "test"
    profile_name                = "dev"
    priority                    = 10
    compute_environment_arn     = "arn:aws:batch:region:acct:compute-environment/test"
    runnable_timeout_seconds    = 3600

    tags = {
      Env = "test"
    }
  }

  assert {
    condition     = aws_batch_job_queue.ec2.priority == 10
    error_message = "Priority not set correctly"
  }

  assert {
    condition = aws_batch_job_queue.ec2.compute_environment_order[0].compute_environment != ""
    error_message = "Compute environment must be attached"
  }

  assert {
    condition = aws_batch_job_queue.ec2.job_state_time_limit_action[0].max_time_seconds == 3600
    error_message = "Runnable timeout not wired correctly"
  }
}