############################################
#   Layer with all dependencies, except Syft
############################################

resource "aws_s3_bucket_object" "lambda_dependencies" {
  bucket = "my-bucket-with-lambda-dependencies-2"
  key    = "${filemd5("lambda-layers/all-dep/all-dep.zip")}.zip"
  source = "lambda-layers/all-dep/all-dep.zip"
}

module "lambda_layer_all_dependencies" {
  source = "terraform-aws-modules/lambda/aws"

  create_layer = true

  layer_name          = "lambda-layer-all-dependencies"
  description         = "Lambda layer with all dependencies except Syft(deployed from S3)"
  compatible_runtimes = ["python3.6"]

  create_package = false
  s3_existing_package = {
    bucket = "my-bucket-with-lambda-dependencies-2"
    key    = aws_s3_bucket_object.lambda_dependencies.id
  }
}


############################
#    Lambda Layer with syft
############################


//resource "aws_s3_bucket_object" "lambda_dependencies" {
//  bucket = "my-bucket-with-lambda-dependencies"
//  key    = "${filemd5("lambda-layers/all-dep/all-dep.zip")}.zip"
//  source = "lambda-layers/all-dep/all-dep.zip"
//}
//
//module "lambda_layer_all_dependencies" {
//  source = "terraform-aws-modules/lambda/aws"
//
//  create_layer = true
//
//  layer_name          = "lambda-layer-all-dependencies"
//  description         = "Lambda layer with all dependencies except Syft(deployed from S3)"
//  compatible_runtimes = ["python3.7"]
//
//  create_package = false
//  s3_existing_package = {
//    bucket = "my-bucket-with-lambda-dependencies"
//    key    = aws_s3_bucket_object.lambda_dependencies.id
//  }
//}

