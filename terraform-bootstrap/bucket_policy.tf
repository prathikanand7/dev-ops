resource "aws_s3_bucket_policy" "tf_state_policy" {
  bucket = aws_s3_bucket.tf_state.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = var.terraform_users
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${aws_s3_bucket.tf_state.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Principal = {
          AWS = var.terraform_users
        }
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.tf_state.arn
        ]
      }
    ]
  })
}
