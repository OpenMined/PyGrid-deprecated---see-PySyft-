module "dynamodb_table" {
  source = "terraform-aws-modules/dynamodb-table/aws"

  name     = "pygrid-network-websocket-connections"
  hash_key = "workerId"

  attributes = [
    {
      name = "workerId"
      type = "S" // String
    }
  ]
}