################################
# Account ID (for bucket naming)
################################

data "aws_caller_identity" "current" {}

################################
# S3 Bucket
################################

resource "aws_s3_bucket" "batch_payloads" {
  bucket = "${var.project_name}-batch-payloads-${data.aws_caller_identity.current.account_id}"

  tags = merge(var.tags, {
    Name = "${var.project_name}-batch-payloads"
  })
}
