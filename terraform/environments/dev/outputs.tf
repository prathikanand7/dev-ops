
output "rds_engine" {
  value = module.rds.db_instance_engine # see note below
}

output "rds_name" {
  value = module.rds.db_instance_name
}

output "vpc_azs" {
  value = module.vpc.azs
}

output "vpc_private_subnets" {
  value = module.vpc.private_subnets_cidr_blocks
}

output "vpc_public_subnets" {
  value = module.vpc.public_subnets_cidr_blocks
}