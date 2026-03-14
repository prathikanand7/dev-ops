# Module: batch_job_definition_ec2

Creates an AWS Batch **EC2 job definition** and the IAM job role granting it S3 read/write access.

## Resources

| Resource | Description |
|---|---|
| `aws_iam_role.batch_job_role` | IAM role assumed by the container task |
| `aws_iam_role_policy.batch_job_s3` | Inline policy granting S3 ListBucket / GetObject / PutObject |
| `aws_batch_job_definition.ec2` | EC2 job definition |

## Usage

```hcl
module "batch_job_definition_ec2" {
  source = "./modules/batch_job_definition_ec2"

  project_name    = "lifewatch"
  container_image = "020858641931.dkr.ecr.eu-west-1.amazonaws.com/r-notebook-worker:latest"
  s3_bucket_arn   = module.s3.bucket_arn

  vcpus      = 2
  memory_mib = 16384

  tags = { Environment = "dev" }
}
```

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `project_name` | `string` | — | Prefix for resource names and tags |
| `container_image` | `string` | — | Full ECR image URI |
| `container_command` | `list(string)` | `["python","worker.py"]` | Container startup command |
| `vcpus` | `number` | `2` | vCPUs per job |
| `memory_mib` | `number` | `16384` | Memory per job in MiB |
| `s3_bucket_arn` | `string` | — | ARN of the S3 payload bucket |
| `tags` | `map(string)` | `{}` | Tags applied to all resources |

## Outputs

| Name | Description |
|---|---|
| `job_definition_arn` | ARN of the EC2 job definition |
| `job_definition_name` | Name of the EC2 job definition |
| `job_role_arn` | ARN of the IAM job role |

## Notes

- `environment` is intentionally left empty. The Lambda trigger injects `JOB_ID` and `S3_JOB_PREFIX` dynamically via `containerOverrides` at submission time.
- EC2 job definitions use the legacy top-level `vcpus`/`memory` fields (not `resourceRequirements`), which is the correct format for `platform_capabilities = ["EC2"]`.
