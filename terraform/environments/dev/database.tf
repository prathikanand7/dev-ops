module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  # We changed this name to force a clean, new database creation
  identifier = "my-app-database"

  engine               = "mysql"
  engine_version       = "8.0"
  family               = "mysql8.0"
  major_engine_version = "8.0"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  
  db_name  = "myappdb"
  username = "dbadmin"
  manage_master_user_password = true

  subnet_ids             = module.vpc.private_subnets
  vpc_security_group_ids = [module.vpc.default_security_group_id]
}