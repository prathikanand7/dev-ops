variable "project_name" {
  description = "Project name prefix used for resource naming and tagging."
  type        = string
}

variable "max_vcpus" {
  description = "Maximum number of vCPUs the EC2 compute environment can scale to."
  type        = number
  default     = 256
}

variable "allocation_strategy" {
  description = "EC2 fleet allocation strategy. Recommended: BEST_FIT_PROGRESSIVE."
  type        = string
  default     = "BEST_FIT_PROGRESSIVE"
}

variable "instance_types" {
  description = "List of EC2 instance types Batch may use."
  type        = list(string)
  default     = ["m6i.2xlarge", "m6i.4xlarge", "m5.2xlarge", "m5.4xlarge"]
}

variable "subnet_ids" {
  description = "List of subnet IDs in which EC2 instances will be launched."
  type        = list(string)
}

variable "security_group_ids" {
  description = "List of security group IDs to attach to EC2 instances."
  type        = list(string)
}

variable "ebs_volume_size_gb" {
  description = "Root EBS volume size in GiB attached via the launch template."
  type        = number
  default     = 200
}

variable "ebs_iops" {
  description = "Provisioned IOPS for the root EBS gp3 volume."
  type        = number
  default     = 3000
}

variable "ebs_throughput" {
  description = "Throughput (MiB/s) for the root EBS gp3 volume."
  type        = number
  default     = 125
}

variable "tags" {
  description = "Map of tags applied to all resources in this module."
  type        = map(string)
  default     = {}
}
