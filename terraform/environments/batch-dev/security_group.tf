# Security Group for Batch
resource "aws_security_group" "batch_security_group" {
  name_prefix = "lifewatch-batch-sg"
  description = "Security group for Lifewatch Batch compute environment"
  vpc_id      = aws_vpc.my_app_vpc.id

  egress {
    description = "HTTPS to VPC endpoints"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    description = "HTTPS to internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "HTTP to internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "lifewatch-batch-sg"
  }
}

# Security Group for VPC Endpoints
resource "aws_security_group" "vpc_endpoint_sg" {
  name_prefix = "lifewatch-vpc-endpoint-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = aws_vpc.my_app_vpc.id

  ingress {
    description     = "HTTPS from Batch security group"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.batch_security_group.id]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "lifewatch-vpc-endpoint-sg"
  }
}