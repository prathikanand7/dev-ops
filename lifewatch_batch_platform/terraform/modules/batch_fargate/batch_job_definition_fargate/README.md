# Module: batch_job_definition_fargate

Creates an AWS Batch **Fargate job definition** and the IAM job role granting it S3 read/write access.

## Resources

| Resource | Description |
|---|---|
| `aws_iam_role.batch_job_role` | IAM role assumed by the container task |
| `aws_iam_role_policy.batch_job_s3` | Inline policy granting S3 ListBucket / GetObject / PutObject |
| `aws_batch_job_definition.fargate` | Fargate job definition |

## Usage

```hcl
module "batch_job_definition_fargate" {
  source = "./modules/batch_job_definition_fargate"

  project_name      = "lifewatch"
  container_image   = "020858641931.dkr.ecr.eu-west-1.amazonaws.com/r-notebook-worker:latest"
  execution_role_arn = "arn:aws:iam::020858641931:role/BatchEcsTaskExecutionRole"
  s3_bucket_arn     = module.s3.bucket_arn

  vcpus                 = 1
  memory_mib            = 8192
  ephemeral_storage_gib = 21

  tags = { Environment = "dev" }
}
```

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `project_name` | `string` | — | Prefix for resource names and tags |
| `container_image` | `string` | — | Full ECR image URI |
| `container_command` | `list(string)` | `["python","worker.py"]` | Container startup command |
| `vcpus` | `number` | `1` | vCPUs per job |
| `memory_mib` | `number` | `8192` | Memory per job in MiB |
| `ephemeral_storage_gib` | `number` | `21` | Ephemeral storage per task in GiB |
| `execution_role_arn` | `string` | — | ARN of the ECS task execution role |
| `s3_bucket_arn` | `string` | — | ARN of the S3 payload bucket |
| `tags` | `map(string)` | `{}` | Tags applied to all resources |

## Outputs

| Name | Description |
|---|---|
| `job_definition_arn` | ARN of the Fargate job definition |
| `job_definition_name` | Name of the Fargate job definition |
| `job_role_arn` | ARN of the IAM job role |

## Notes

- `environment` is intentionally left empty in the job definition. The Lambda trigger injects `JOB_ID` and `S3_JOB_PREFIX` dynamically at submission time via `containerOverrides`.
