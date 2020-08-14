provider "aws" {
  region                  = "ap-south-1"
  shared_credentials_file = "$HOME/.aws/credentials"
}


module "api_gateway" {
  source = "terraform-aws-modules/apigateway-v2/aws"

  name          = "PygridNodeAPIGateway-http"
  description   = "Node HTTP API Gateway"
  protocol_type = "HTTP"

  create_api_domain_name = false

  integrations = {
    "$default" = {
      lambda_arn = module.lambda.this_lambda_function_arn
    }
  }
}


module "lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 1.0"

  function_name = "pygrid-node"
  description   = "Node hosted by UCSF"
  handler       = "wsgi.app"        #TODO: change this -------------------------------
  runtime       = "python3.6"
  publish       = true # To automate increasing versions

  source_path = "../../apps/node/src/"  #TODO: change this -------------------------------

#   tags = {
#     Name = ""
#   }

  allowed_triggers = {
    AllowExecutionFromAPIGateway = {
      service    = "apigateway"
      source_arn = "${module.api_gateway.this_apigatewayv2_api_execution_arn}/*/*"
    }
  }
}

module "lambda_alias" {
  source  = "terraform-aws-modules/lambda/aws//modules/alias"
  version = "~> 1.0"

  name = "prod"

  function_name = module.lambda.this_lambda_function_name

  # Set function_version when creating alias to be able to deploy using it,
  # because AWS CodeDeploy doesn't understand $LATEST as CurrentVersion.
  function_version = module.lambda.this_lambda_function_version
}

# Data sources to get VPC and subnets
data "aws_vpc" "default" {
  default = true
}

data "aws_subnet_ids" "all" {
  vpc_id = data.aws_vpc.default.id
}

module "aurora" {
  source = "terraform-aws-modules/rds-aurora/aws"

  name                  = "aurora-serverless-database"
  engine                = "aurora"
  engine_mode           = "serverless"
  replica_scale_enabled = false
  replica_count         = 0

  subnets       = data.aws_subnet_ids.all.ids
  vpc_id        = data.aws_vpc.default.id
  instance_type = "db.r4.large"

  enable_http_endpoint = true   # Enable Data API

  scaling_configuration = {
    auto_pause               = true
    max_capacity             = 64  #ACU
    min_capacity             = 2   #ACU
    seconds_until_auto_pause = 300
    timeout_action           = "ForceApplyCapacityChange"
  }
}
