resource "aws_secretsmanager_secret" "database-secret" {
  name                    = "pygrid-network-rds-admin"
  description             = "PyGrid network database credentials"
}

# TODO: Add it as a .tfvar
variable "rds_credentials" {
  default = {
    username = "admin"
    password = "random-strings"
  }
  type = map(string)
}

resource "aws_secretsmanager_secret_version" "secret" {
  secret_id     = aws_secretsmanager_secret.database-secret.id
  secret_string = jsonencode(var.rds_credentials)
}
