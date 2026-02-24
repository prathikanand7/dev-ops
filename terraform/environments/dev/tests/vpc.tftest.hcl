// subnets
run "private_subnet_count" {
  command = plan
  assert {
    condition     = length(output.vpc_private_subnets) == 2
    error_message = "Expected 2 private subnets"
  }
}

run "public_subnet_count" {
  command = plan
  assert {
    condition     = length(output.vpc_public_subnets) == 2
    error_message = "Expected 2 public subnets"
  }
}

// CIDR blocks
run "private_subnet_cidr" {
  command = plan
  assert {
    condition = alltrue([
      can(regex("^10\\.0\\.1\\.0/24$", output.vpc_private_subnets[0])),
      can(regex("^10\\.0\\.2\\.0/24$", output.vpc_private_subnets[1]))
    ])
    error_message = "Private subnet CIDRs are incorrect"
  }
}

run "public_subnet_cidr" {
  command = plan
  assert {
    condition = alltrue([
      can(regex("^10\\.0\\.101\\.0/24$", output.vpc_public_subnets[0])),
      can(regex("^10\\.0\\.102\\.0/24$", output.vpc_public_subnets[1]))
    ])
    error_message = "Public subnet CIDRs are incorrect"
  }
}

// NAT Gateway
# run "nat_gateway_enabled" {
#   command = plan
#   assert {
#     condition     = module.vpc.enable_nat_gateway == true
#     error_message = "NAT Gateway must be enabled"
#   }
# }