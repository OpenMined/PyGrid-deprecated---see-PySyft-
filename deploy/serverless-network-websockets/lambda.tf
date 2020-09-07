locals {
  function_path    = "../../apps/network/src/"
  function_handler = "wsgi.lambda_handler"
  connect_route    = "$connect"
  disconnect_route = "$disconnect"
}

module "lambda" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "pyGrid-network-websocket-function"
  runtime       = "python3.7"
  description   = "PyGrid Network websocket server"
  publish       = true # To automate increasing versions

  source_path = local.function_path
  handler     = local.function_handler

  create_role = false
  lambda_role = aws_iam_role.pygrid-network-websocket-role.arn

  environment_variables = {
    DYNAMODB_TABLE_NAME = module.dynamodb_table.this_dynamodb_table_id
    WEBSOCKET_INVOKE_URL = aws_apigatewayv2_stage.Test.invoke_url
  }

  allowed_triggers = {
    AllowExecutionFromAPIGateway_onConnect = {
      service    = "apigateway"
      source_arn = "${module.api_gateway.this_apigatewayv2_api_execution_arn}/*/${local.connect_route}"
    },
    AllowExecutionFromAPIGateway_onDisconnect = {
      service    = "apigateway"
      source_arn = "${module.api_gateway.this_apigatewayv2_api_execution_arn}/*/${local.disconnect_route}"
    }
  }
}

module "lambda_alias_chat_app_connect" {
  source        = "terraform-aws-modules/lambda/aws//modules/alias"
  version       = "~> 1.0"
  name          = "prod"
  function_name = module.lambda.this_lambda_function_name
  # Set function_version when creating alias to be able to deploy using it,
  # because AWS CodeDeploy doesn't understand $LATEST as CurrentVersion.
  function_version = module.lambda.this_lambda_function_version
}

