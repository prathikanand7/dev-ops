run "security_groups" {
  command = plan

  variables {
    project_name = "test"
    vpc_id       = "vpc-123"

    tags = {
      Env = "test"
    }
  }

  ################################
  # Security Groups Exist
  ################################

  assert {
    condition     = aws_security_group.batch.vpc_id == "vpc-123"
    error_message = "Batch SG must be in correct VPC"
  }

  assert {
    condition     = aws_security_group.endpoints.vpc_id == "vpc-123"
    error_message = "Endpoint SG must be in correct VPC"
  }

  ################################
  # Batch Egress Rules
  ################################

  assert {
    condition     = aws_security_group_rule.batch_https_out.from_port == 443
    error_message = "Batch HTTPS egress must use port 443"
  }

  assert {
    condition     = aws_security_group_rule.batch_https_out.protocol == "tcp"
    error_message = "Batch HTTPS must use TCP"
  }

  assert {
    condition     = aws_security_group_rule.batch_http_out.from_port == 80
    error_message = "Batch HTTP egress must use port 80"
  }

  assert {
    condition     = aws_security_group_rule.batch_9000_out.from_port == 9000
    error_message = "Batch TCP 9000 egress missing"
  }

  ################################
  # Batch -> Endpoint Rule
  ################################

  assert {
    condition     = aws_security_group_rule.batch_to_endpoints.type == "egress"
    error_message = "Batch to endpoint must be egress"
  }

  assert {
    condition     = aws_security_group_rule.batch_to_endpoints.from_port == 443
    error_message = "Batch to endpoint must use HTTPS"
  }

  assert {
    condition     = aws_security_group_rule.batch_to_endpoints.protocol == "tcp"
    error_message = "Batch to endpoint must use TCP"
  }

  ################################
  # Endpoint Ingress Rule
  ################################

  assert {
    condition     = aws_security_group_rule.endpoint_ingress_batch.type == "ingress"
    error_message = "Endpoint rule must be ingress"
  }

  assert {
    condition     = aws_security_group_rule.endpoint_ingress_batch.from_port == 443
    error_message = "Endpoint ingress must use HTTPS"
  }

  assert {
    condition     = aws_security_group_rule.endpoint_ingress_batch.protocol == "tcp"
    error_message = "Endpoint ingress must use TCP"
  }

  ################################
  # Endpoint Egress Rule
  ################################

  assert {
    condition     = aws_security_group_rule.endpoint_egress_all.protocol == "-1"
    error_message = "Endpoint egress must allow all protocols"
  }

  assert {
    condition     = aws_security_group_rule.endpoint_egress_all.cidr_blocks[0] == "0.0.0.0/0"
    error_message = "Endpoint must allow outbound to internet"
  }
}