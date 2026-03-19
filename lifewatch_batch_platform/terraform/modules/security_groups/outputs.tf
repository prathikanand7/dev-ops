output "batch_security_group_id" {
  value = aws_security_group.batch.id
}

output "endpoint_security_group_id" {
  value = aws_security_group.endpoints.id
}
