# Versioning problems, for now create bucket using GUI

# module "s3_bucket" {
#   source = "terraform-aws-modules/s3-bucket/aws"

#   bucket = "my-bucket-with-lambda-dependencies-2"
#   acl    = "private"

#   versioning = {
#     enabled = true
#   }
# }