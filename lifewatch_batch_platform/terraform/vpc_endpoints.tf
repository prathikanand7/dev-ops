# S3 Gateway Endpoint
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.my_app_vpc.id
  service_name      = "com.amazonaws.eu-west-1.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = [
    aws_route_table.my_app_vpc_default.id
  ]


  tags = {
    Name = "lifewatch-s3-endpoint"
  }
}

# ECR Docker
resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = aws_vpc.my_app_vpc.id
  service_name        = "com.amazonaws.eu-west-1.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids = [
    aws_subnet.my_app_vpc_public_eu_west_1a.id,
    aws_subnet.my_app_vpc_public_eu_west_1b.id
  ]

  security_group_ids = [aws_security_group.vpc_endpoint_sg.id]

  tags = {
    Name = "lifewatch-ecr-dkr-endpoint"
  }
}

# ECR API
resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = aws_vpc.my_app_vpc.id
  service_name        = "com.amazonaws.eu-west-1.ecr.api"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids = [
    aws_subnet.my_app_vpc_public_eu_west_1a.id,
    aws_subnet.my_app_vpc_public_eu_west_1b.id
  ]

  security_group_ids = [aws_security_group.vpc_endpoint_sg.id]

  tags = {
    Name = "lifewatch-ecr-api-endpoint"
  }
}

# CloudWatch Logs
resource "aws_vpc_endpoint" "logs" {
  vpc_id              = aws_vpc.my_app_vpc.id
  service_name        = "com.amazonaws.eu-west-1.logs"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids = [
    aws_subnet.my_app_vpc_public_eu_west_1a.id,
    aws_subnet.my_app_vpc_public_eu_west_1b.id
  ]

  security_group_ids = [aws_security_group.vpc_endpoint_sg.id]

  tags = {
    Name = "lifewatch-logs-endpoint"
  }
}

# ECS
resource "aws_vpc_endpoint" "ecs" {
  vpc_id              = aws_vpc.my_app_vpc.id
  service_name        = "com.amazonaws.eu-west-1.ecs"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids = [
    aws_subnet.my_app_vpc_public_eu_west_1a.id,
    aws_subnet.my_app_vpc_public_eu_west_1b.id
  ]

  security_group_ids = [aws_security_group.vpc_endpoint_sg.id]

  tags = {
    Name = "lifewatch-ecs-endpoint"
  }
}

# ECS Agent
resource "aws_vpc_endpoint" "ecs_agent" {
  vpc_id              = aws_vpc.my_app_vpc.id
  service_name        = "com.amazonaws.eu-west-1.ecs-agent"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids = [
    aws_subnet.my_app_vpc_public_eu_west_1a.id,
    aws_subnet.my_app_vpc_public_eu_west_1b.id
  ]

  security_group_ids = [aws_security_group.vpc_endpoint_sg.id]

  tags = {
    Name = "lifewatch-ecs-agent-endpoint"
  }
}

# ECS Telemetry
resource "aws_vpc_endpoint" "ecs_telemetry" {
  vpc_id              = aws_vpc.my_app_vpc.id
  service_name        = "com.amazonaws.eu-west-1.ecs-telemetry"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids = [
    aws_subnet.my_app_vpc_public_eu_west_1a.id,
    aws_subnet.my_app_vpc_public_eu_west_1b.id
  ]

  security_group_ids = [aws_security_group.vpc_endpoint_sg.id]

  tags = {
    Name = "lifewatch-ecs-telemetry-endpoint"
  }
}
