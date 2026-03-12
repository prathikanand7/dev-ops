################################
# Fargate Compute Environment
################################

locals {
  # Referencing endpoint IDs in a local forces Terraform to resolve the VPC
  # endpoints before this resource, without using depends_on with a variable.
  endpoint_dependency = length(var.vpc_endpoint_dependency_ids) > 0 ? join(",", var.vpc_endpoint_dependency_ids) : ""
}

resource "aws_batch_compute_environment" "fargate" {
  name  = "${var.project_name}-fargate-environment"
  type  = "MANAGED"
  state = "ENABLED"

  compute_resources {
    type               = "FARGATE"
    max_vcpus          = var.max_vcpus
    subnets            = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  tags = merge(var.tags, {
    Name             = "${var.project_name}-fargate-environment"
    _EndpointOrderer = local.endpoint_dependency
  })
}
