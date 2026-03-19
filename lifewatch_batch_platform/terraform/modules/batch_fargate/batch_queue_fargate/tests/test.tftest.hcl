run "fargate_job_queue" {
  command = plan

  variables {
    project_name             = "test"
    profile_name             = "dev"
    priority                 = 5
    compute_environment_arn  = "arn:aws:batch:region:acct:compute-environment/test"
    runnable_timeout_seconds = 1800

    tags = {
      Env = "test"
    }
  }

  assert {
    condition     = aws_batch_job_queue.fargate.priority == 5
    error_message = "Priority incorrect"
  }

  assert {
    condition     = aws_batch_job_queue.fargate.compute_environment_order[0].order == 1
    error_message = "Compute environment order must be 1"
  }

  assert {
    condition     = aws_batch_job_queue.fargate.job_state_time_limit_action[0].action == "CANCEL"
    error_message = "Runnable jobs must cancel after timeout"
  }
}
