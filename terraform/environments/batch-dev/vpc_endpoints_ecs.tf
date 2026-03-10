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
