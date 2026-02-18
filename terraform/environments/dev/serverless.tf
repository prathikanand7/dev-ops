# --- Dummy Lambda Setup ---
data "archive_file" "dummy_lambda" {
  type        = "zip"
  output_path = "${path.module}/dummy_lambda.zip"
  source {
    content  = "def lambda_handler(event, context):\n    return {'statusCode': 200, 'body': 'Auth Logic Here'}"
    filename = "index.py"
  }
}

resource "aws_iam_role" "lambda_exec" {
  name = "app_lambda_exec_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Action = "sts:AssumeRole", Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" } }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Auth Lambdas ---
locals {
  auth_lambdas = ["register", "login", "logout", "forgot-password", "change-password", "refresh"]
}

resource "aws_lambda_function" "auth_lambdas" {
  for_each         = toset(local.auth_lambdas)
  function_name    = "auth_${each.key}_lambda"
  handler          = "index.lambda_handler"
  runtime          = "python3.10"
  role             = aws_iam_role.lambda_exec.arn
  filename         = data.archive_file.dummy_lambda.output_path
  source_code_hash = data.archive_file.dummy_lambda.output_base64sha256
}

# --- EKS Internal Load Balancer ---
resource "aws_lb" "eks_internal_nlb" {
  name               = "eks-internal-nlb"
  internal           = true
  load_balancer_type = "network"
  subnets            = module.vpc.private_subnets
}

resource "aws_lb_target_group" "eks_tg" {
  name        = "eks-target-group"
  port        = 80
  protocol    = "TCP"
  vpc_id      = module.vpc.vpc_id
  target_type = "ip" 
}

resource "aws_lb_listener" "eks_listener" {
  load_balancer_arn = aws_lb.eks_internal_nlb.arn
  port              = "80"
  protocol          = "TCP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.eks_tg.arn
  }
}

# --- API Gateway ---
resource "aws_apigatewayv2_api" "http_api" {
  name          = "my-app-http-api"
  protocol_type = "HTTP"
}

# --- Route Auth Traffic to Lambdas ---
resource "aws_apigatewayv2_integration" "auth_lambda_integrations" {
  for_each         = toset(local.auth_lambdas)
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.auth_lambdas[each.key].invoke_arn
}

resource "aws_apigatewayv2_route" "auth_routes" {
  for_each  = toset(local.auth_lambdas)
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /api/v1/auth/${each.key}"
  target    = "integrations/${aws_apigatewayv2_integration.auth_lambda_integrations[each.key].id}"
}

resource "aws_lambda_permission" "api_gw_auth" {
  for_each      = toset(local.auth_lambdas)
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auth_lambdas[each.key].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

# --- Route EKS Traffic via VPC Link ---
resource "aws_apigatewayv2_vpc_link" "eks_vpc_link" {
  name               = "eks-vpc-link"
  security_group_ids = [module.vpc.default_security_group_id]
  subnet_ids         = module.vpc.private_subnets
}

resource "aws_apigatewayv2_integration" "eks_integration" {
  api_id             = aws_apigatewayv2_api.http_api.id
  integration_type   = "HTTP_PROXY"
  integration_uri    = aws_lb_listener.eks_listener.arn
  integration_method = "ANY"
  connection_type    = "VPC_LINK"
  connection_id      = aws_apigatewayv2_vpc_link.eks_vpc_link.id
}

resource "aws_apigatewayv2_route" "eks_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "ANY /api/eks/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.eks_integration.id}"
}