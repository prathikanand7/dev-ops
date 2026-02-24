run "rds_mysql_engine" {
  command = plan
  assert {
    condition = output.rds_engine == "mysql"
    error_message = "RDS engine must be MySQL"
  }
}

run "rds_name" {
  command = plan
  assert {
    condition = output.rds_name == "myappdb"
    error_message = "RDS must not be public"
  }
}


