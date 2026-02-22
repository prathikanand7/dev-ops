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