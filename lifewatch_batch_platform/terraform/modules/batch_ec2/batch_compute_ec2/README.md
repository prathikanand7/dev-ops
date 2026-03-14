# Module: batch_compute_ec2

Creates an AWS Batch **managed EC2 compute environment**, including all required IAM roles, an instance profile, and a hardened gp3 launch template.

## Resources

| Resource | Description |
|---|---|
| `aws_iam_role.batch_service_role` | IAM role assumed by the Batch service |
| `aws_iam_role.ec2_instance_role` | IAM role assumed by EC2 instances in the environment |
| `aws_iam_instance_profile.ec2_instance_profile` | Instance profile wrapping the EC2 instance role |
| `aws_launch_template.batch_ec2` | Launch template with encrypted gp3 root volume and IMDSv2 |
| `aws_batch_compute_environment.ec2` | Managed EC2 compute environment |

## Usage

```hcl
module "batch_compute_ec2" {
  source = "./modules/batch_compute_ec2"

  project_name        = "lifewatch"
  max_vcpus           = 256
  instance_types      = ["m6i.2xlarge", "m6i.4xlarge", "m5.2xlarge", "m5.4xlarge"]
  ebs_volume_size_gb  = 200
  subnet_ids          = module.vpc.private_subnet_ids
  security_group_ids  = [module.security_groups.batch_sg_id]

  tags = { Environment = "dev" }
}
```

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `project_name` | `string` | — | Prefix for resource names and tags |
| `max_vcpus` | `number` | `256` | Maximum vCPUs the environment can scale to |
| `allocation_strategy` | `string` | `BEST_FIT_PROGRESSIVE` | EC2 fleet allocation strategy |
| `instance_types` | `list(string)` | `["m6i.2xlarge", ...]` | EC2 instance types Batch may launch |
| `subnet_ids` | `list(string)` | — | Subnets for EC2 instance placement |
| `security_group_ids` | `list(string)` | — | Security groups attached to EC2 instances |
| `ebs_volume_size_gb` | `number` | `200` | Root EBS volume size in GiB |
| `ebs_iops` | `number` | `3000` | Provisioned IOPS for the gp3 volume |
| `ebs_throughput` | `number` | `125` | Throughput (MiB/s) for the gp3 volume |
| `tags` | `map(string)` | `{}` | Tags applied to all resources |

## Outputs

| Name | Description |
|---|---|
| `compute_environment_arn` | ARN of the EC2 compute environment |
| `compute_environment_name` | Name of the EC2 compute environment |
| `batch_service_role_arn` | ARN of the Batch service IAM role |
| `ec2_instance_profile_arn` | ARN of the EC2 instance profile |
| `launch_template_id` | ID of the attached launch template |

## Notes

- `desired_vcpus` is excluded from the Terraform lifecycle to prevent drift — Batch manages this value dynamically while jobs are running.
- IMDSv2 (`http_tokens = required`) is enforced on all instances via the launch template.
