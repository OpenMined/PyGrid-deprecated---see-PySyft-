# TODO: Add it as a .tfvar
variable "rds_credentials" {
  default = {
    username = "admin"
    password = "random-strings"
  }
  type = map(string)
}

variable "database_name" {
  default = "mydb"
}