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
  name = "lifewatch-lambda-full-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.batch_payloads.arn,
          "${aws_s3_bucket.batch_payloads.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "batch:SubmitJob",
          "batch:DescribeJobs"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:GetLogEvents",
          "logs:DescribeLogStreams"
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
      STANDARD_JOB_QUEUE       = aws_batch_job_queue.lifewatch_fargate_job_queue.name
      STANDARD_JOB_DEFINITION  = aws_batch_job_definition.lifewatch_fargate_job_definition.name
      EC2_200GB_JOB_QUEUE      = aws_batch_job_queue.lifewatch_ec2_200gb_job_queue.name
      EC2_200GB_JOB_DEFINITION = aws_batch_job_definition.lifewatch_ec2_200gb_job_definition.name
    }
  }
}

resource "aws_lambda_function" "job_status" {
  function_name    = "lifewatch-job-status"
  role             = aws_iam_role.lambda_role.arn
  handler          = "status.lambda_handler"
  runtime          = "python3.11"
  filename         = "status_lambda.zip"
  source_code_hash = filebase64sha256("status_lambda.zip")
  timeout          = 10 # Good practice to give it a little breathing room

  environment {
    variables = {
      BUCKET = aws_s3_bucket.batch_payloads.bucket
    }
  }
}

resource "aws_lambda_function" "job_logs" {
  function_name    = "lifewatch-job-logs"
  role             = aws_iam_role.lambda_role.arn
  handler          = "logs.lambda_handler"
  runtime          = "python3.11"
  filename         = "logs_lambda.zip"
  source_code_hash = filebase64sha256("logs_lambda.zip")
  timeout          = 10

  environment {
    variables = {
      BUCKET = aws_s3_bucket.batch_payloads.bucket
    }
  }
}

resource "aws_lambda_function" "job_results" {
  function_name    = "lifewatch-job-results"
  role             = aws_iam_role.lambda_role.arn
  handler          = "results.lambda_handler"
  runtime          = "python3.11"
  filename         = "results_lambda.zip"
  source_code_hash = filebase64sha256("results_lambda.zip")
  timeout          = 10

  environment {
    variables = {
      BUCKET = aws_s3_bucket.batch_payloads.bucket
    }
  }
}