################################
# S3 Gateway Endpoint
################################

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = [var.private_route_table_id]

  tags = merge(var.tags, {
    Name = "${var.project_name}-s3-endpoint"
  })
}

################################
# ECR Docker
################################

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids         = var.private_subnet_ids
  security_group_ids = [var.endpoint_security_group]

  tags = merge(var.tags, {
    Name = "${var.project_name}-ecr-dkr-endpoint"
  })
}

################################
# ECR API
################################

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids         = var.private_subnet_ids
  security_group_ids = [var.endpoint_security_group]

  tags = merge(var.tags, {
    Name = "${var.project_name}-ecr-api-endpoint"
  })
}

################################
# CloudWatch Logs
################################

resource "aws_vpc_endpoint" "logs" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.logs"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids         = var.private_subnet_ids
  security_group_ids = [var.endpoint_security_group]

  tags = merge(var.tags, {
    Name = "${var.project_name}-logs-endpoint"
  })
}

################################
# ECS
################################

resource "aws_vpc_endpoint" "ecs" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.ecs"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids         = var.private_subnet_ids
  security_group_ids = [var.endpoint_security_group]

  tags = merge(var.tags, {
    Name = "${var.project_name}-ecs-endpoint"
  })
}

################################
# ECS Agent
################################

resource "aws_vpc_endpoint" "ecs_agent" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.ecs-agent"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids         = var.private_subnet_ids
  security_group_ids = [var.endpoint_security_group]

  tags = merge(var.tags, {
    Name = "${var.project_name}-ecs-agent-endpoint"
  })
}

################################
# ECS Telemetry
################################

resource "aws_vpc_endpoint" "ecs_telemetry" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.ecs-telemetry"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids         = var.private_subnet_ids
  security_group_ids = [var.endpoint_security_group]

  tags = merge(var.tags, {
    Name = "${var.project_name}-ecs-telemetry-endpoint"
  })
}