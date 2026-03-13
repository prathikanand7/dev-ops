################################
# VPC
################################

module "vpc" {
  source = "../../modules/vpc"

  project_name          = var.project_name
  vpc_cidr              = var.vpc_cidr
  public_subnet_a_cidr  = var.public_subnet_a_cidr
  public_subnet_b_cidr  = var.public_subnet_b_cidr
  private_subnet_a_cidr = var.private_subnet_a_cidr
  private_subnet_b_cidr = var.private_subnet_b_cidr
  region                = var.region
  internet_cidr         = "0.0.0.0/0"

  tags = var.tags
}

################################
# Security Groups
################################

module "security_groups" {
  source = "../../modules/security_groups"

  project_name = var.project_name
  vpc_id       = module.vpc.vpc_id

  tags = var.tags
}

################################
# VPC Endpoints
################################

module "vpc_endpoints" {
  source = "../../modules/vpc_endpoints"

  project_name            = var.project_name
  vpc_id                  = module.vpc.vpc_id
  region                  = var.region
  private_subnet_ids      = module.vpc.private_subnets
  private_route_table_id  = module.vpc.private_route_table_id
  endpoint_security_group = module.security_groups.endpoint_security_group_id

  tags = var.tags
}

################################
# S3
################################

module "s3_batch_payloads" {
  source = "../../modules/s3_batch_payloads"

  project_name = var.project_name
  tags         = var.tags
}

################################
# Batch - Fargate
################################

module "batch_compute_fargate" {
  source = "../../modules/batch_fargate/batch_compute_fargate"

  project_name       = var.project_name
  max_vcpus          = var.fargate_max_vcpus
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [module.security_groups.batch_security_group_id]

  vpc_endpoint_dependency_ids = [
    module.vpc_endpoints.s3_endpoint_id,
    module.vpc_endpoints.ecr_dkr_endpoint_id,
    module.vpc_endpoints.ecr_api_endpoint_id,
    module.vpc_endpoints.logs_endpoint_id,
  ]

  tags = var.tags
}

module "batch_job_definition_fargate" {
  source = "../../modules/batch_fargate/batch_job_definition_fargate"

  project_name          = var.project_name
  container_image       = var.container_image
  execution_role_arn    = var.batch_execution_role_arn
  s3_bucket_arn         = module.s3_batch_payloads.bucket_arn
  vcpus                 = var.fargate_vcpus
  memory_mib            = var.fargate_memory_mib
  ephemeral_storage_gib = var.fargate_ephemeral_storage_gib

  tags = var.tags
}

module "batch_queue_fargate" {
  source = "../../modules/batch_fargate/batch_queue_fargate"

  project_name            = var.project_name
  compute_environment_arn = module.batch_compute_fargate.compute_environment_arn

  tags = var.tags
}

################################
# Batch - EC2
################################

module "batch_compute_ec2" {
  source = "../../modules/batch_ec2/batch_compute_ec2"

  project_name       = var.project_name
  max_vcpus          = var.ec2_max_vcpus
  instance_types     = var.ec2_instance_types
  ebs_volume_size_gb = var.ec2_ebs_volume_size_gb
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [module.security_groups.batch_security_group_id]

  tags = var.tags
}

module "batch_job_definition_ec2" {
  source = "../../modules/batch_ec2/batch_job_definition_ec2"

  project_name    = var.project_name
  container_image = var.container_image
  s3_bucket_arn   = module.s3_batch_payloads.bucket_arn
  vcpus           = var.ec2_vcpus
  memory_mib      = var.ec2_memory_mib

  tags = var.tags
}

module "batch_queue_ec2" {
  source = "../../modules/batch_ec2/batch_queue_ec2"

  project_name            = var.project_name
  compute_environment_arn = module.batch_compute_ec2.compute_environment_arn

  tags = var.tags
}

################################
# Lambda — IAM (shared)
################################

module "lambda_iam" {
  source = "../../modules/lambda_iam"

  project_name  = var.project_name
  s3_bucket_arn = module.s3_batch_payloads.bucket_arn

  tags = var.tags
}

################################
# Lambda — Functions
################################

module "lambda_batch_trigger" {
  source = "../../modules/lambda/lambda_batch_trigger"

  project_name    = var.project_name
  lambda_role_arn = module.lambda_iam.role_arn
  filename        = var.lambda_trigger_filename
  s3_bucket_name  = module.s3_batch_payloads.bucket_name

  standard_job_queue_name      = module.batch_queue_fargate.job_queue_name
  standard_job_definition_name = module.batch_job_definition_fargate.job_definition_name
  ec2_job_queue_name           = module.batch_queue_ec2.job_queue_name
  ec2_job_definition_name      = module.batch_job_definition_ec2.job_definition_name
}

module "lambda_job_status" {
  source = "../../modules/lambda/lambda_job_status"

  project_name    = var.project_name
  lambda_role_arn = module.lambda_iam.role_arn
  filename        = var.lambda_status_filename
  s3_bucket_name  = module.s3_batch_payloads.bucket_name
}

module "lambda_job_logs" {
  source = "../../modules/lambda/lambda_job_logs"

  project_name    = var.project_name
  lambda_role_arn = module.lambda_iam.role_arn
  filename        = var.lambda_logs_filename
  s3_bucket_name  = module.s3_batch_payloads.bucket_name
}

module "lambda_job_results" {
  source = "../../modules/lambda/lambda_job_results"

  project_name    = var.project_name
  lambda_role_arn = module.lambda_iam.role_arn
  filename        = var.lambda_results_filename
  s3_bucket_name  = module.s3_batch_payloads.bucket_name
}

################################
# API Gateway
################################

module "api_gateway" {
  source = "../../modules/api_gateway"

  project_name             = var.project_name
  stage_name               = var.stage_name
  batch_trigger_lambda_arn = module.lambda_batch_trigger.invoke_arn
  job_status_lambda_arn    = module.lambda_job_status.invoke_arn
  job_logs_lambda_arn      = module.lambda_job_logs.invoke_arn
  job_results_lambda_arn   = module.lambda_job_results.invoke_arn
}

################################
# API Key & Usage Plan
################################

module "api_key_usage_plan" {
  source = "../../modules/api_key_usage_plan"

  api_id                 = module.api_gateway.api_id
  stage_name             = module.api_gateway.stage_name
  lifewatch_key_name     = var.api_key_name
  usage_plan_name        = var.usage_plan_name
  usage_plan_description = var.usage_plan_description
}
