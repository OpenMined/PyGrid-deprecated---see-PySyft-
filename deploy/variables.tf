variable "aws_region" {
  default = "eu-west-2" # London
  type    = string
}

variable "vpc_cidr_block" {
  default = "10.0.0.0/16"
  type = string
}

variable "subnet_cidr_block" {
  default = "10.0.1.0/24"
  type = string
}

variable "amis" {
  type = map(string)
  default = {
    "eu-west-2"  = "ami-00f6a0c18edb19300" # London, Ubuntu AMI
    "ap-south-1" = "ami-02d55cb47e83a99a0" # Mumbai, Ubuntu AMI
    "us-east-1"  = "ami-0ac80df6eff0e70b5" # N. Virginia, Ubuntu AMI
  }
}
