
run "bucket_name_format" {
  command = plan
  assert {
    condition     = can(regex("^my-app-data-bucket-[a-f0-9]+$", output.bucket_name))
    error_message = "Bucket name format invalid"
  }
}