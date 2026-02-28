resource "aws_batch_compute_environment" "lifewatch_fargate_environment" {
  name  = "lifewatch-fargate-environment"
  type  = "MANAGED"
  state = "ENABLED"

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
    aws_vpc_endpoint.s3,
    aws_vpc_endpoint.ecr_dkr,
    aws_vpc_endpoint.ecr_api,
    aws_vpc_endpoint.logs
  ]

  tags = {
    Name = "lifewatch-fargate-environment"
  }
}