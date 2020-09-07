resource "aws_iam_role" "pygrid-network-websocket-role" {
  name               = "pygrid-network-websocket-role"
  assume_role_policy = <<-EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "sts:AssumeRole",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Effect": "Allow",
        "Sid": ""
      }
    ]
  }
  EOF
}

resource "aws_iam_role_policy" "pygrid-network-websockets-lambda-policy" {
  name   = "pygrid-network-websockets-lambda-function-policy"
  role   = aws_iam_role.pygrid-network-websocket-role.id
  policy = <<-EOF
  {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:BatchGetItem",
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:BatchWriteItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:deleteItem"
            ],
            "Resource": "${module.dynamodb_table.this_dynamodb_table_arn}"
        },
        {
            "Action": [
                "logs:*"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Action": [
                "execute-api:ManageConnections"
            ],
            "Effect": "Allow",
            "Resource": "${module.api_gateway.this_apigatewayv2_api_execution_arn}/*"
        }
    ]
  }
  EOF
}