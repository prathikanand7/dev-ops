################################
# Fargate Compute Environment
################################
resource "aws_batch_compute_environment" "fargate" {
  name  = "${var.project_name}-${var.profile_name}-environment"
  type  = "MANAGED"
  state = "ENABLED"
  compute_resources {
    type               = "FARGATE"
    max_vcpus          = var.max_vcpus
    subnets            = var.subnet_ids
    security_group_ids = var.security_group_ids
  }
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.profile_name}-environment"
  })
}
