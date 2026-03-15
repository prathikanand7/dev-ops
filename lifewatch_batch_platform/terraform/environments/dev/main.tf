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
# Locals for dynamic setup
################################
locals {
  job_profiles_data = jsondecode(file("../../../../job_profiles.json"))
  fargate_profiles  = { for k, v in local.job_profiles_data.profiles : k => v if v.backend_type == "FARGATE" }
  ec2_profiles      = { for k, v in local.job_profiles_data.profiles : k => v if v.backend_type == "EC2" }
}

################################
# Batch - Fargate
################################

module "batch_compute_fargate" {
  source   = "../../modules/batch_fargate/batch_compute_fargate"
  for_each = local.fargate_profiles

  project_name       = var.project_name
  profile_name       = each.key
  service_role_arn   = module.batch_iam.batch_service_role_arn
  max_vcpus          = var.fargate_max_vcpus
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [module.security_groups.batch_security_group_id]

  vpc_endpoint_dependency_ids = [
    module.vpc_endpoints.s3_endpoint_id,
  ]

  tags = var.tags
}

module "batch_job_definition_fargate" {
  job_role_arn = module.batch_iam.batch_job_role_arn
  source       = "../../modules/batch_fargate/batch_job_definition_fargate"
  for_each     = local.fargate_profiles

  project_name          = var.project_name
  profile_name          = each.key
  container_image       = var.container_image
  execution_role_arn    = var.batch_execution_role_arn
  s3_bucket_arn         = module.s3_batch_payloads.bucket_arn
  vcpus                 = try(each.value.vcpu, var.fargate_vcpus)
  memory_mib            = try(each.value.memory_mb, var.fargate_memory_mib)
  ephemeral_storage_gib = try(each.value.storage_gb, var.fargate_ephemeral_storage_gib)

  tags = var.tags
}

module "batch_queue_fargate" {
  source   = "../../modules/batch_fargate/batch_queue_fargate"
  for_each = local.fargate_profiles

  project_name            = var.project_name
  profile_name            = each.key
  compute_environment_arn = module.batch_compute_fargate[each.key].compute_environment_arn

  tags = var.tags
}

################################
# Batch - EC2
################################

module "batch_compute_ec2" {
  service_role_arn     = module.batch_iam.batch_service_role_arn
  instance_profile_arn = module.batch_iam.ec2_instance_profile_arn
  source               = "../../modules/batch_ec2/batch_compute_ec2"
  for_each             = local.ec2_profiles

  project_name       = var.project_name
  profile_name       = each.key
  max_vcpus          = var.ec2_max_vcpus
  instance_types     = var.ec2_instance_types
  ebs_volume_size_gb = try(each.value.storage_gb, var.ec2_ebs_volume_size_gb)
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [module.security_groups.batch_security_group_id]

  tags = var.tags
}

module "batch_job_definition_ec2" {
  job_role_arn = module.batch_iam.batch_job_role_arn
  source       = "../../modules/batch_ec2/batch_job_definition_ec2"
  for_each     = local.ec2_profiles

  project_name    = var.project_name
  profile_name    = each.key
  container_image = var.container_image
  s3_bucket_arn   = module.s3_batch_payloads.bucket_arn
  vcpus           = try(each.value.vcpu, var.ec2_vcpus)
  memory_mib      = try(each.value.memory_mb, var.ec2_memory_mib)

  tags = var.tags
}

module "batch_queue_ec2" {
  source   = "../../modules/batch_ec2/batch_queue_ec2"
  for_each = local.ec2_profiles

  project_name            = var.project_name
  profile_name            = each.key
  compute_environment_arn = module.batch_compute_ec2[each.key].compute_environment_arn

  tags = var.tags
}

################################
# Batch - IAM (shared)
################################
module "batch_iam" {
  source = "../../modules/batch_iam"

  project_name  = var.project_name
  s3_bucket_arn = module.s3_batch_payloads.bucket_arn

  tags = var.tags
}

################################
# Lambda - IAM (shared)
################################

module "lambda_iam" {
  source = "../../modules/lambda_iam"

  project_name  = var.project_name
  s3_bucket_arn = module.s3_batch_payloads.bucket_arn

  tags = var.tags
}

################################
# Lambda - Functions
################################

module "lambda_batch_trigger" {
  source = "../../modules/lambda/lambda_batch_trigger"

  project_name    = var.project_name
  lambda_role_arn = module.lambda_iam.role_arn
  filename        = var.lambda_trigger_filename
  s3_bucket_name  = module.s3_batch_payloads.bucket_name

  job_profiles_config_json = jsonencode(merge(
    { for k, v in local.fargate_profiles : k => {
      queue      = module.batch_queue_fargate[k].job_queue_name
      definition = module.batch_job_definition_fargate[k].job_definition_name
      }
    },
    { for k, v in local.ec2_profiles : k => {
      queue      = module.batch_queue_ec2[k].job_queue_name
      definition = module.batch_job_definition_ec2[k].job_definition_name
      }
    }
  ))
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

module "lambda_job_history_list" {
  source = "../../modules/lambda/lambda_job_history_list"

  project_name    = var.project_name
  lambda_role_arn = module.lambda_iam.role_arn
  filename        = var.lambda_history_list_filename
  s3_bucket_name  = module.s3_batch_payloads.bucket_name
}

################################
# API Gateway
################################

module "api_gateway" {
  source = "../../modules/api_gateway"

  project_name                = var.project_name
  stage_name                  = var.stage_name
  batch_trigger_lambda_arn    = module.lambda_batch_trigger.invoke_arn
  job_status_lambda_arn       = module.lambda_job_status.invoke_arn
  job_logs_lambda_arn         = module.lambda_job_logs.invoke_arn
  job_results_lambda_arn      = module.lambda_job_results.invoke_arn
  job_history_list_lambda_arn = module.lambda_job_history_list.invoke_arn
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
  burst_limit            = var.burst_limit
  rate_limit             = var.rate_limit
}
