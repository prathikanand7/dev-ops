output "s3_endpoint_id" {
  description = "ID of the S3 gateway endpoint."
  value       = aws_vpc_endpoint.s3.id
}

output "ecs_endpoint_id" {
  description = "ID of the ECS interface endpoint."
  value       = aws_vpc_endpoint.ecs.id
}

output "ecs_agent_endpoint_id" {
  description = "ID of the ECS agent interface endpoint."
  value       = aws_vpc_endpoint.ecs_agent.id
}
