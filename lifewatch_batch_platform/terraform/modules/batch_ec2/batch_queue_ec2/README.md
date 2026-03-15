# Module: batch_queue_ec2

Creates an AWS Batch **job queue** backed by an EC2 compute environment.

## Resources

| Resource | Description |
|---|---|
| `aws_batch_job_queue.ec2` | EC2 job queue with runnable-timeout action |

## Usage

```hcl
module "batch_queue_ec2" {
  source = "./modules/batch_queue_ec2"

  project_name            = "lifewatch"
  compute_environment_arn = module.batch_compute_ec2.compute_environment_arn
  priority                = 20

  tags = { Environment = "dev" }
}
```

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `project_name` | `string` | — | Prefix for resource names and tags |
| `compute_environment_arn` | `string` | — | ARN of the EC2 compute environment |
| `priority` | `number` | `20` | Queue scheduling priority |
| `runnable_timeout_seconds` | `number` | `600` | Seconds before a stuck RUNNABLE job is cancelled |
| `tags` | `map(string)` | `{}` | Tags applied to all resources |

## Outputs

| Name | Description |
|---|---|
| `job_queue_arn` | ARN of the EC2 job queue |
| `job_queue_name` | Name of the EC2 job queue |

## Notes

- The EC2 queue defaults to `priority = 20`, higher than the Fargate queue (`10`), matching the original design where EC2 jobs are preferred for heavy workloads.
