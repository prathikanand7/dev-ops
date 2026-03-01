resource "aws_s3_bucket" "batch_payloads" {
  bucket = "lifewatch-batch-payloads-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "lifewatch-batch-payloads"
  }
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "batch_job_role" {
  name = "BatchJobS3Role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "batch_job_s3_policy" {
  name = "BatchJobS3Access"
  role = aws_iam_role.batch_job_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.batch_payloads.arn}/*"
      }
    ]
  })
}