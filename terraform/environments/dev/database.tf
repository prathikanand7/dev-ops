module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  # A brand new identifier so AWS treats this as a 100% new entity
  identifier = "my-app-mysql-cluster"

  engine               = "mysql"
  engine_version       = "8.0"
  family               = "mysql8.0"
  major_engine_version = "8.0"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  
  db_name  = "myappdb"
  username = "dbadmin"
  manage_master_user_password = true

  # THE FIX: Explicitly forcing a uniquely named subnet group
  create_db_subnet_group = true
  db_subnet_group_name   = "my-app-mysql-subnet-group-v2"
  subnet_ids             = module.vpc.private_subnets

  vpc_security_group_ids = [module.vpc.default_security_group_id]
}