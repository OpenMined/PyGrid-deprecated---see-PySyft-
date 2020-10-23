from terrascript import Module
from terrascript import Output
import terrascript.provider as provider
import terrascript.resource as resource
import terrascript.data as data

from .aws_role_policies import *

# TODO: THIS FUNCTION WOULD BE MOVED TO API SIDE.
# THIS HANDLES THE DEPLOYMENT OF THE INFRASTRUCTURE
# CURRENTLY, IT IS HERE FOR DEVELOPMENT PURPOSE ONLY.

var = lambda x: "${" + x + "}"
var_module = lambda x, y: var(f"module.{x._name}.{y}")


def serverless_deployment(
    tfscript, app, db_username, db_password, python_runtime="python3.6"
):
    """
    app (str) : The app("node"/"network") which is to be deployed.
    db_username (str): Deployed database username
    db_password (str): Deployed database password
    """

    # TODO: THINK OF BETTER AND SHORTER NAMES.
    # TODO: ADD TAGS TO EVERY RESOURCE.

    # ----- VPC ----#

    vpc = data.aws_vpc("default", default=True)
    tfscript += vpc

    aws_subnet_ids = data.aws_subnet_ids("all", vpc_id=var(vpc.id))
    tfscript += aws_subnet_ids

    # ----- Lambda Layer -----#

    s3_bucket = resource.aws_s3_bucket(
        f"{app}-lambda-layer-bucket",
        bucket=f"pygrid-{app}-lambda-layer-bucket",
        acl="private",
        versioning={"enabled": True},
    )
    tfscript += s3_bucket

    dependencies_zip_path = "deploy/serverless-network/lambda-layer/check.zip"

    s3_bucket_object = resource.aws_s3_bucket_object(
        f"pygrid-{app}-lambda-layer",
        bucket=s3_bucket.bucket,
        key=var('filemd5("{}")'.format(dependencies_zip_path)) + ".zip",
        source=dependencies_zip_path,
        depends_on=[f"aws_s3_bucket.{s3_bucket._name}"],
    )
    tfscript += s3_bucket_object

    lambda_layer = resource.aws_lambda_layer_version(
        f"pygrid-{app}-lambda-layer",
        layer_name=f"pygrid-{app}-dependencies",
        compatible_runtimes=[python_runtime],
        s3_bucket=s3_bucket_object.bucket,
        s3_key=s3_bucket_object.key,
        depends_on=[f"aws_s3_bucket_object.{s3_bucket_object._name}"],
    )
    tfscript += lambda_layer

    # ----- API GateWay -----#

    api_gateway = Module(
        "api_gateway",
        source="terraform-aws-modules/apigateway-v2/aws",
        name=f"pygrid-{app}-http",
        protocol_type="HTTP",
        create_api_domain_name=False,
        integrations={
            "$default": {"lambda_arn": "${module.lambda.this_lambda_function_arn}"}
        },
    )
    tfscript += api_gateway

    # ------ IAM role ------#

    lambda_iam_role = resource.aws_iam_role(
        f"pygrid-{app}-lambda-role",
        name=f"pygrid-{app}-lambda-role",
        assume_role_policy="""{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Effect": "Allow",
                    "Sid": ""
                }
            ]
        }""",
    )
    tfscript += lambda_iam_role

    policy1 = resource.aws_iam_role_policy(
        "AWSLambdaVPCAccessExecutionRole",
        name="AWSLambdaVPCAccessExecutionRole",
        role=var(lambda_iam_role.id),
        policy=aws_lambda_vpc_execution_role_policy,
    )
    tfscript += policy1

    policy2 = resource.aws_iam_role_policy(
        "CloudWatchLogsFullAccess",
        name="CloudWatchLogsFullAccess",
        role=var(lambda_iam_role.id),
        policy=cloud_watch_logs_full_access_policy,
    )
    tfscript += policy2

    policy3 = resource.aws_iam_role_policy(
        "AmazonRDSDataFullAcess",
        name="AmazonRDSDataFullAcess",
        role=var(lambda_iam_role.id),
        policy=amazon_rds_data_full_access_policy,
    )
    tfscript += policy3

    # ----- Database -----#

    db_parameter_group = resource.aws_db_parameter_group(
        "aurora_db_parameter_group",
        name=f"pygrid-{app}-aurora-db-parameter-group",
        family="aurora5.6",
        description=f"pygrid-{app}-aurora-db-parameter-group",
    )
    tfscript += db_parameter_group

    rds_cluster_parameter_group = resource.aws_rds_cluster_parameter_group(
        "aurora_cluster_56_parameter_group",
        name=f"pygrid-{app}-aurora-cluster-parameter-group",
        family="aurora5.6",
        description=f"pygrid-{app}-aurora-cluster-parameter-group",
    )
    tfscript += rds_cluster_parameter_group

    database = Module(
        "aurora",
        source="terraform-aws-modules/rds-aurora/aws",
        name=f"pygrid-{app}-database",
        engine="aurora",
        engine_mode="serverless",
        replica_scale_enabled=False,
        replica_count=0,
        subnets=var(aws_subnet_ids.ids),
        vpc_id=var(vpc.id),
        instance_type="db.t2.micro",
        enable_http_endpoint=True,  # Enable Data API,
        apply_immediately=True,
        skip_final_snapshot=True,
        storage_encrypted=True,
        database_name="pygridDB",
        username=db_username,
        password=db_password,
        db_parameter_group_name=var(db_parameter_group.id),
        db_cluster_parameter_group_name=var(rds_cluster_parameter_group.id),
        scaling_configuration={
            "auto_pause": True,
            "max_capacity": 64,  # ACU
            "min_capacity": 2,  # ACU
            "seconds_until_auto_pause": 300,
            "timeout_action": "ForceApplyCapacityChange",
        },
    )
    tfscript += database

    # ----- Secret Manager ----#

    db_secret_manager = resource.aws_secretsmanager_secret(
        "db-secret",
        name=f"pygrid-{app}-rds",
        description=f"PyGrid {app} database credentials",
    )
    tfscript += db_secret_manager

    # TODO: THE PASSWORDS ARE WRITTEN TO STATE FILES
    # wHICH SHOUOLD NOT BE THE CASE

    db_secret_version = resource.aws_secretsmanager_secret_version(
        "db-secret-version",
        secret_id=var(db_secret_manager.id),
        secret_string="jsonencode({})".format(
            {"username": db_username, "password": db_password}
        ),
    )
    tfscript += db_secret_version

    # ----- Lambda Function -----#

    lambda_func = Module(
        "lambda",
        source="terraform-aws-modules/lambda/aws",
        function_name=f"pygrid-{app}",
        publish=True,  # To automate increasing versions
        runtime=python_runtime,
        source_path=f"./apps/{app}/src",
        handler="deploy.app",
        create_role=False,
        lambda_role=var(lambda_iam_role.arn),
        layers=[var(lambda_layer.arn)],
        environment_variables={
            "DB_NAME": database.database_name,
            "DB_CLUSTER_ARN": var_module(database, "this_rds_cluster_arn"),
            "DB_SECRET_ARN": var(db_secret_manager.arn),
            # "SECRET_KEY"     : "Do-we-need-this-in-deployed-version"  # TODO: Clarify this
        },
        allowed_triggers={
            "AllowExecutionFromAPIGateway": {
                "service": "apigateway",
                "source_arn": "{}/*/*".format(
                    var_module(api_gateway, "this_apigatewayv2_api_execution_arn")
                ),
            }
        },
    )
    tfscript += lambda_func

    lambda_alias = Module(
        "lambda_alias",
        source="terraform-aws-modules/lambda/aws//modules/alias",
        name="prod",
        function_name=var_module(lambda_func, "this_lambda_function_name"),
        function_version=var_module(lambda_func, "this_lambda_function_version"),
    )
    tfscript += lambda_alias

    return tfscript
