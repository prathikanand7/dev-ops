################################
# Batch Security Group
################################

resource "aws_security_group" "batch" {
  name_prefix = "${var.project_name}-batch-sg"
  description = "Security group for Batch compute"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.project_name}-batch-sg"
  })
}

################################
# Batch -> Internet (HTTPS)
################################

resource "aws_security_group_rule" "batch_https_out" {
  type              = "egress"
  description       = "HTTPS to internet"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.batch.id
}

################################
# Batch → Internet (HTTP)
################################

resource "aws_security_group_rule" "batch_http_out" {
  type              = "egress"
  description       = "HTTP to internet"
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.batch.id
}

################################
# Batch → VPC Endpoints (HTTPS)
################################

resource "aws_security_group_rule" "batch_to_endpoints" {
  type                     = "egress"
  description              = "HTTPS to VPC endpoints"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.batch.id
  source_security_group_id = aws_security_group.endpoints.id
}

################################
# Endpoint Security Group
################################

resource "aws_security_group" "endpoints" {
  name_prefix = "${var.project_name}-endpoint-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.project_name}-endpoint-sg"
  })
}

################################
# Endpoint ← Batch (HTTPS)
################################

resource "aws_security_group_rule" "endpoint_ingress_batch" {
  type                     = "ingress"
  description              = "HTTPS from Batch compute"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.endpoints.id
  source_security_group_id = aws_security_group.batch.id
}

################################
# Endpoint → AWS Services
################################

resource "aws_security_group_rule" "endpoint_egress_all" {
  type              = "egress"
  description       = "Outbound to AWS services"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.endpoints.id
}