terraform {
  backend "s3" {
    bucket         = "lifewatch-terraform-state-eu-west-1"
    key            = "lifewatch-high-compute/dev/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "lifewatch-terraform-locks"
    encrypt        = true
  }
}