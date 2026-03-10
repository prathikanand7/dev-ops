resource "aws_iam_role" "lambda_role" {
  name = "lifewatch-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.batch_payloads.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["batch:SubmitJob"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "batch_trigger" {
  function_name    = "lifewatch-batch-trigger"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  filename         = "lambda.zip"
  source_code_hash = filebase64sha256("lambda.zip")

  environment {
    variables = {
      BUCKET                   = aws_s3_bucket.batch_payloads.bucket
      STANDARD_JOB_QUEUE       = local.batch_execution_profiles.standard.job_queue
      STANDARD_JOB_DEFINITION  = local.batch_execution_profiles.standard.job_definition
      EC2_200GB_JOB_QUEUE      = local.batch_execution_profiles.ec2_200gb.job_queue
      EC2_200GB_JOB_DEFINITION = local.batch_execution_profiles.ec2_200gb.job_definition
    }
  }
}
