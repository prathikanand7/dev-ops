run "vpc" {
  command = plan

  variables {
    project_name           = "lifewatch"
    region                 = "eu-west-1"
    vpc_cidr               = "10.0.0.0/16"
    public_subnet_a_cidr   = "10.0.103.0/24"
    public_subnet_b_cidr   = "10.0.102.0/24"
    private_subnet_a_cidr  = "10.0.1.0/24"
    private_subnet_b_cidr  = "10.0.2.0/24"
    internet_cidr          = "0.0.0.0/0"

    tags = {
      Environment = "dev"
      Project     = "lifewatch"
      ManagedBy   = "terraform"
    }
  }

  ################################
  # VPC
  ################################
  assert {
    condition     = aws_vpc.main.cidr_block == "10.0.0.0/16"
    error_message = "VPC must have correct CIDR block"
  }

  assert {
    condition     = aws_vpc.main.enable_dns_hostnames == true
    error_message = "DNS hostnames must be enabled"
  }

  assert {
    condition     = aws_vpc.main.enable_dns_support == true
    error_message = "DNS support must be enabled"
  }

  ################################
  # Public Subnets
  ################################
  assert {
    condition     = aws_subnet.public_a.cidr_block == "10.0.103.0/24"
    error_message = "Public subnet A CIDR mismatch"
  }

  assert {
    condition     = aws_subnet.public_a.map_public_ip_on_launch == true
    error_message = "Public subnet A must assign public IPs"
  }

  assert {
    condition     = aws_subnet.public_b.cidr_block == "10.0.102.0/24"
    error_message = "Public subnet B CIDR mismatch"
  }

  assert {
    condition     = aws_subnet.public_b.map_public_ip_on_launch == true
    error_message = "Public subnet B must assign public IPs"
  }

  ################################
  # Private Subnets
  ################################
  assert {
    condition     = aws_subnet.private_a.cidr_block == "10.0.1.0/24"
    error_message = "Private subnet A CIDR mismatch"
  }

  assert {
    condition     = aws_subnet.private_b.cidr_block == "10.0.2.0/24"
    error_message = "Private subnet B CIDR mismatch"
  }

  assert {
    condition     = aws_internet_gateway.igw.tags["Name"] != ""
    error_message = "Internet Gateway must have a Name tag"
  }
}