################################
# Global
################################
project_name = "lifewatch"
region       = "eu-west-1"
tags = {
  Environment = "dev"
  Project     = "lifewatch"
  ManagedBy   = "terraform"
}

################################
# VPC
################################
vpc_cidr              = "10.0.0.0/16"
public_subnet_a_cidr  = "10.0.103.0/24"
public_subnet_b_cidr  = "10.0.102.0/24"
private_subnet_a_cidr = "10.0.1.0/24"
private_subnet_b_cidr = "10.0.2.0/24"

################################
# Batch — Fargate
################################
fargate_max_vcpus             = 256
fargate_vcpus                 = 1
fargate_memory_mib            = 8192
fargate_ephemeral_storage_gib = 21

################################
# Batch — EC2
################################
ec2_max_vcpus          = 256
ec2_instance_types     = ["m6i.2xlarge", "m6i.4xlarge", "m5.2xlarge", "m5.4xlarge"]
ec2_ebs_volume_size_gb = 200
ec2_vcpus              = 2
ec2_memory_mib         = 16384

################################
# Lambda
################################
lambda_trigger_filename = "../../backend_lambda_artifacts/lambda.zip"
lambda_status_filename  = "../../backend_lambda_artifacts/status_lambda.zip"
lambda_logs_filename    = "../../backend_lambda_artifacts/logs_lambda.zip"
lambda_results_filename = "../../backend_lambda_artifacts/results_lambda.zip"

################################
# API Gateway
################################
stage_name             = "dev"
api_key_name           = "lifewatch-api-key"
usage_plan_name        = "lifewatch-usage-plan"
usage_plan_description = "Usage plan for Lifewatch REST API"
burst_limit            = 5
rate_limit             = 10
