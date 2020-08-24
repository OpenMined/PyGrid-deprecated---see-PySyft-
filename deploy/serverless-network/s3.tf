
resource "aws_s3_bucket" "bucket" {
  bucket = "bucket-with-pygrid-network-dependencies"
  acl    = "private"

  versioning {
    enabled = true
  }
}

resource "aws_s3_bucket_object" "lambda_dependencies" {
  bucket = aws_s3_bucket.bucket.bucket
  key    = "${filemd5("lambda-layers/all-dep/all-dep.zip")}.zip"
  source = "lambda-layers/all-dep/all-dep.zip"
}