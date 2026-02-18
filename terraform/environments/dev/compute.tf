module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "my-app-cluster"
  # Change this from "1.29" to "1.30"
  cluster_version = "1.30" 

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    general = {
      desired_size   = 2
      instance_types = ["t3.medium"]
    }
  }
}