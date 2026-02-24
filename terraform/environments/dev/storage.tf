resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "data_bucket" {
  bucket = "my-app-data-bucket-${random_id.bucket_suffix.hex}"
}