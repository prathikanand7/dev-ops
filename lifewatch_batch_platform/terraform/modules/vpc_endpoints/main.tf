################################
# S3 Gateway Endpoint
################################

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = [var.private_route_table_id]

  tags = merge(var.tags, {
    Name = "${var.project_name}-s3-endpoint"
  })
}
