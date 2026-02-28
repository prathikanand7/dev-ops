# S3 Gateway Endpoint
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.my_app_vpc.id
  service_name = "com.amazonaws.eu-west-1.s3"

  tags = {
    Name = "lifewatch-s3-endpoint"
  }
}

# ECR Docker
resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id            = aws_vpc.my_app_vpc.id
  service_name      = "com.amazonaws.eu-west-1.ecr.dkr"
  vpc_endpoint_type = "Interface"

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
  vpc_id            = aws_vpc.my_app_vpc.id
  service_name      = "com.amazonaws.eu-west-1.ecr.api"
  vpc_endpoint_type = "Interface"

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
  vpc_id            = aws_vpc.my_app_vpc.id
  service_name      = "com.amazonaws.eu-west-1.logs"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    aws_subnet.my_app_vpc_public_eu_west_1a.id,
    aws_subnet.my_app_vpc_public_eu_west_1b.id
  ]

  security_group_ids = [aws_security_group.vpc_endpoint_sg.id]

  tags = {
    Name = "lifewatch-logs-endpoint"
  }
}