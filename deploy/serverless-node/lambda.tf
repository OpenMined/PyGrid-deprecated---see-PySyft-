locals {
  function_path    = "../../apps/node/src/"
  function_handler = "deploy.app"
}

module "lambda" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "pygrid-node"
  description   = "Node hosted by UCSF"
  publish       = true # To automate increasing versions

  runtime     = "python3.8"
  source_path = local.function_path
  handler     = local.function_handler

  timeout = 60*2  # 2 minutes
  memory_size = 1000 # 1000 MB

  create_role = false
  lambda_role = aws_iam_role.pygrid-network-lambda-role.arn

  layers = [
    module.lambda_layer.this_lambda_layer_arn,
  ]

  environment_variables = {
    MOUNT_PATH = "/mnt${aws_efs_access_point.node-access-points.root_directory[0].path}"
  }
  allowed_triggers = {
    AllowExecutionFromAPIGateway = {
      service    = "apigateway"
      source_arn = "${module.api_gateway.this_apigatewayv2_api_execution_arn}/*/*"
    }
  }

  vpc_subnet_ids         = data.aws_subnet_ids.all.ids
  vpc_security_group_ids = [aws_security_group.allow_efs.id]

  //  Note: file_system_arn is arn of access point
  file_system_arn = aws_efs_access_point.node-access-points.arn
  file_system_local_mount_path = "/mnt${aws_efs_access_point.node-access-points.root_directory[0].path}"
}

module "lambda_alias" {
  source = "terraform-aws-modules/lambda/aws//modules/alias"

  name          = "prod"
  function_name = module.lambda.this_lambda_function_name

  # Set function_version when creating alias to be able to deploy using it,
  # because AWS CodeDeploy doesn't understand $LATEST as CurrentVersion.
  function_version = module.lambda.this_lambda_function_version
}
