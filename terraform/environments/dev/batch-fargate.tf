# VPC
resource "aws_vpc" "my_app_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  instance_tenancy     = "default"

  tags = {
    Name = "my-app-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "my_app_igw" {
  vpc_id = aws_vpc.my_app_vpc.id

  tags = {
    Name = "my-app-igw"
  }
}

# Route Table
resource "aws_route_table" "my_app_vpc_default" {
  vpc_id = aws_vpc.my_app_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.my_app_igw.id
  }

  tags = {
    Name = "my-app-vpc-default"
  }
}

# Subnets
resource "aws_subnet" "my_app_vpc_public_eu_west_1a" {
  vpc_id            = aws_vpc.my_app_vpc.id
  cidr_block        = "10.0.103.0/24"
  availability_zone = "eu-west-1a"

  tags = {
    Name = "my-app-vpc-public-eu-west-1a"
  }
}

resource "aws_subnet" "my_app_vpc_public_eu_west_1b" {
  vpc_id            = aws_vpc.my_app_vpc.id
  cidr_block        = "10.0.102.0/24"
  availability_zone = "eu-west-1b"

  tags = {
    Name = "my-app-vpc-public-eu-west-1b"
  }
}

# Route Table Associations
resource "aws_route_table_association" "subnet_1a_association" {
  subnet_id      = aws_subnet.my_app_vpc_public_eu_west_1a.id
  route_table_id = aws_route_table.my_app_vpc_default.id
}

resource "aws_route_table_association" "subnet_1b_association" {
  subnet_id      = aws_subnet.my_app_vpc_public_eu_west_1b.id
  route_table_id = aws_route_table.my_app_vpc_default.id
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

# Security Group for Batch (secure with VPC endpoints)
resource "aws_security_group" "batch_security_group" {
  name_prefix = "lifewatch-batch-sg"
  description = "Security group for Lifewatch Batch compute environment"
  vpc_id      = aws_vpc.my_app_vpc.id

  # Minimal egress rules when using VPC endpoints
  egress {
    description = "HTTPS to VPC endpoints"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"] # Only within VPC
  }

  egress {
    description = "HTTPS to internet (for any external dependencies)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "HTTP to internet (for package downloads if needed)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "lifewatch-batch-sg"
  }
}

# VPC Endpoints for secure AWS service communication
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.my_app_vpc.id
  service_name = "com.amazonaws.eu-west-1.s3"

  tags = {
    Name = "lifewatch-s3-endpoint"
  }
}

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

# AWS Batch Compute Environment - lifewatch-fargate-environment
resource "aws_batch_compute_environment" "lifewatch_fargate_environment" {
  compute_environment_name = "lifewatch-fargate-environment"
  type                     = "MANAGED"
  state                    = "ENABLED"

  compute_resources {
    type = "FARGATE"

    subnets = [
      aws_subnet.my_app_vpc_public_eu_west_1a.id,
      aws_subnet.my_app_vpc_public_eu_west_1b.id
    ]

    security_group_ids = [
      aws_security_group.batch_security_group.id
    ]

    max_vcpus = 256
  }

  depends_on = [
    aws_subnet.my_app_vpc_public_eu_west_1a,
    aws_subnet.my_app_vpc_public_eu_west_1b,
    aws_security_group.batch_security_group,
    aws_vpc_endpoint.s3,
    aws_vpc_endpoint.ecr_dkr,
    aws_vpc_endpoint.ecr_api,
    aws_vpc_endpoint.logs
  ]

  tags = {
    Name = "lifewatch-fargate-environment"
  }
}

# AWS Batch Job Queue - lifewatch-fargate-job-queue
resource "aws_batch_job_queue" "lifewatch_fargate_job_queue" {
  name     = "lifewatch-fargate-job-queue"
  state    = "ENABLED"
  priority = 1

  compute_environment_order {
    order               = 1
    compute_environment = aws_batch_compute_environment.lifewatch_fargate_environment.arn
  }

  job_state_time_limit_action {
    state            = "RUNNABLE"
    action           = "CANCEL"
    max_time_seconds = 600
    reason           = "MISCONFIGURATION:COMPUTE_ENVIRONMENT_MAX_RESOURCE"
  }

  tags = {
    Name = "lifewatch-fargate-job-queue"
  }
}

# AWS Batch Job Definition - lifewatch-fargate-job-definition
resource "aws_batch_job_definition" "lifewatch_fargate_job_definition" {
  name = "lifewatch-fargate-job-definition"
  type = "container"

  platform_capabilities = ["FARGATE"]

  container_properties = jsonencode({
    image = "020858641931.dkr.ecr.eu-west-1.amazonaws.com/r-notebook-worker:latest"

    command = ["echo", "Hello world. I am running the job"]

    fargatePlatformConfiguration = {
      platformVersion = "LATEST"
    }

    networkConfiguration = {
      assignPublicIp = "ENABLED"
    }

    resourceRequirements = [
      {
        type  = "VCPU"
        value = "1.0"
      },
      {
        type  = "MEMORY"
        value = "2048"
      }
    ]

    ephemeralStorage = {
      sizeInGiB = 21
    }

    runtimePlatform = {
      cpuArchitecture       = "X86_64"
      operatingSystemFamily = "LINUX"
    }

    executionRoleArn = "arn:aws:iam::020858641931:role/BatchEcsTaskExecutionRole"
  })

  tags = {
    Name = "lifewatch-fargate-job-definition"
  }
}
