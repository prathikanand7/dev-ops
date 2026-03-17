# Module: batch_queue_fargate

Creates an AWS Batch **job queue** backed by a Fargate compute environment.

## Resources

| Resource | Description |
|---|---|
| `aws_batch_job_queue.fargate` | Fargate job queue with runnable-timeout action |

## Usage

```hcl
module "batch_queue_fargate" {
  source = "./modules/batch_queue_fargate"

  project_name            = "lifewatch"
  compute_environment_arn = module.batch_compute_fargate.compute_environment_arn
  priority                = 10

  tags = { Environment = "dev" }
}
```

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `project_name` | `string` | — | Prefix for resource names and tags |
| `compute_environment_arn` | `string` | — | ARN of the Fargate compute environment |
| `priority` | `number` | `10` | Queue scheduling priority |
| `runnable_timeout_seconds` | `number` | `600` | Seconds before a stuck RUNNABLE job is cancelled |
| `tags` | `map(string)` | `{}` | Tags applied to all resources |

## Outputs

| Name | Description |
|---|---|
| `job_queue_arn` | ARN of the Fargate job queue |
| `job_queue_name` | Name of the Fargate job queue |
