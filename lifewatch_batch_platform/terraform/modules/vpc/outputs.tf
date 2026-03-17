output "vpc_id" {
  description = "ID of the VPC."
  value       = aws_vpc.main.id
}

output "public_subnets" {
  description = "List of public subnet IDs (AZ a and b)."
  value       = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

output "private_subnets" {
  description = "List of private subnet IDs (AZ a and b)."
  value       = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}

output "public_subnet_a_id" {
  description = "ID of public subnet in AZ a."
  value       = aws_subnet.public_a.id
}

output "public_subnet_b_id" {
  description = "ID of public subnet in AZ b."
  value       = aws_subnet.public_b.id
}

output "private_subnet_a_id" {
  description = "ID of private subnet in AZ a."
  value       = aws_subnet.private_a.id
}

output "private_subnet_b_id" {
  description = "ID of private subnet in AZ b."
  value       = aws_subnet.private_b.id
}

output "public_route_table_id" {
  description = "ID of the public route table."
  value       = aws_route_table.public.id
}

output "private_route_table_id" {
  description = "ID of the private route table."
  value       = aws_route_table.private.id
}

output "nat_gateway_id" {
  description = "ID of the NAT gateway."
  value       = aws_nat_gateway.nat.id
}

output "internet_gateway_id" {
  description = "ID of the internet gateway."
  value       = aws_internet_gateway.igw.id
}
