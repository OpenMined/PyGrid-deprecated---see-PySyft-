provider "aws" {
  region                  = var.region
  shared_credentials_file = "$HOME/.aws/credentials"
}

module "api_gateway" {
  source = "terraform-aws-modules/apigateway-v2/aws"

  name                       = "pyGrid-network-websocket-apiGateway"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"

  create_api_domain_name = false
  create_default_stage   = false

  integrations = {
    "$connect" = {
      integration_type   = "AWS_PROXY"
      integration_method = "POST"
      lambda_arn         = module.lambda.this_lambda_function_invoke_arn
    },
    "$disconnect" = {
      integration_type   = "AWS_PROXY"
      integration_method = "POST"
      lambda_arn         = module.lambda.this_lambda_function_invoke_arn
    }
  }
}

resource "aws_apigatewayv2_stage" "Test" {
  api_id      = module.api_gateway.this_apigatewayv2_api_id
  name        = "Test"
  auto_deploy = true
}