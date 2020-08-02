variable "aws_region" {
  default = "eu-west-2" # London
  type    = string
}

variable "aws_credintials" {
  default = {
    access_key = "XXXXXXXXXXXXXXXXXXXX"
    secret_key = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  }
  type = map
}
