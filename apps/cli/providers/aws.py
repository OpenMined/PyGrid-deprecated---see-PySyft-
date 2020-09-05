import boto3
import click
from PyInquirer import prompt

from ..utils import Config, styles

## MARK: regions and instances takes some time to be loaded (5-7 sec)
EC2 = boto3.client("ec2")
REGIONS = [region["RegionName"] for region in EC2.describe_regions()["Regions"]]
INSTANCES = [
    instance["InstanceType"]
    for instance in EC2.describe_instance_types()["InstanceTypes"]
]


def get_aws_config():
    """Getting the configration required for deployment on AWs.

    Returns:
        Config: Simple Config with the user inputs
    """

    region = prompt(
        [
            {
                "type": "list",
                "name": "region",
                "message": "Please select your desired AWS region",
                "default": "us-east-1",
                "choices": REGIONS,
            },
        ],
        style=styles.second,
    )["region"]

    instance_type = prompt(
        [
            {
                "type": "list",
                "name": "instance",
                "message": "Please select your desired AWS instance type",
                "default": "t2.micro",
                "choices": INSTANCES,
            },
        ],
        style=styles.second,
    )["instance"]

    ## VPC
    vpc_cidr_block = prompt(
        [
            {
                "type": "input",
                "name": "vpc_cidr_block",
                "message": "Please provide VPC cidr block",
                "default": "10.0.0.0/16",
                # TODO: 'validate': make sure it's a correct ip format
            },
        ],
        style=styles.second,
    )["vpc_cidr_block"]

    ## subnets
    subnet_cidr_block = prompt(
        [
            {
                "type": "input",
                "name": "subnet_cidr_block",
                "message": "Please provide Subnet cidr block",
                "default": "10.0.0.0/24",
                # TODO: 'validate': make sure it's a correct ip format
            },
        ],
        style=styles.second,
    )["subnet_cidr_block"]

    return Config(
        region=region,
        instance_type=instance_type,
        vpc_cidr_block=vpc_cidr_block,
        subnet_cidr_block=subnet_cidr_block,
    )
