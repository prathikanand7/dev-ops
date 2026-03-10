locals {
  batch_execution_profiles = {
    standard = {
      job_queue      = aws_batch_job_queue.lifewatch_fargate_job_queue.name
      job_definition = aws_batch_job_definition.lifewatch_fargate_job_definition.name
    }
    ec2_200gb = {
      job_queue      = aws_batch_job_queue.lifewatch_ec2_200gb_job_queue.name
      job_definition = aws_batch_job_definition.lifewatch_ec2_200gb_job_definition.name
    }
  }
}
