resource "aws_s3_bucket" "dep" {
  bucket = "my-bucket-with-lambda-node-dependencies"
  acl    = "private"

  versioning {
    enabled = true
  }
}

resource "aws_s3_bucket_object" "lambda_dependencies" {
  bucket = "my-bucket-with-lambda-node-dependencies"
  key    = "${filemd5("lambda-layers/all-dep/all-dep.zip")}.zip"
  source = "lambda-layers/all-dep/all-dep.zip"
}