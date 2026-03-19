run "vpc_endpoints" {
  command = plan

  variables {
    project_name            = "test"
    region                  = "eu-west-1"
    vpc_id                  = "vpc-123"
    private_route_table_id  = "rtb-123"
    private_subnet_ids      = ["subnet-1", "subnet-2"]
    endpoint_security_group = "sg-123"

    tags = {
      Env = "test"
    }
  }

  # S3 endpoint type
  assert {
    condition     = aws_vpc_endpoint.s3.vpc_endpoint_type == "Gateway"
    error_message = "S3 must be gateway endpoint"
  }
}
