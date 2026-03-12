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
  vpc_id                  = aws_vpc.my_app_vpc.id
  cidr_block              = "10.0.103.0/24"
  availability_zone       = "eu-west-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "my-app-vpc-public-eu-west-1a"
  }
}

resource "aws_subnet" "my_app_vpc_public_eu_west_1b" {
  vpc_id                  = aws_vpc.my_app_vpc.id
  cidr_block              = "10.0.102.0/24"
  availability_zone       = "eu-west-1b"
  map_public_ip_on_launch = true

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
