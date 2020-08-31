resource "aws_secretsmanager_secret" "database-secret" {
  name                    = "pygrid-network-rds-admin"
  description             = "PyGrid network database credentials"
}


resource "aws_secretsmanager_secret_version" "secret" {
  secret_id     = aws_secretsmanager_secret.database-secret.id
  secret_string = jsonencode(var.rds_credentials)
}
