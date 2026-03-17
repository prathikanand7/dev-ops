output "bucket_name" {
  description = "Name of the S3 batch payloads bucket."
  value       = aws_s3_bucket.batch_payloads.bucket
}

output "bucket_arn" {
  description = "ARN of the S3 batch payloads bucket."
  value       = aws_s3_bucket.batch_payloads.arn
}
