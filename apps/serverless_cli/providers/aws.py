import boto3
import click
from PyInquirer import prompt

from ..utils import Config, styles


def vpc_regions_list():
    vpc_client = boto3.client("ec2")
    return [region["RegionName"] for region in vpc_client.describe_regions()["Regions"]]


def az_list(region):
    vpc_client = boto3.client("ec2", region_name=region)
    return [
        {"name": zone["ZoneName"]}
        for zone in vpc_client.describe_availability_zones(
            Filters=[{"Name": "region-name", "Values": [region]}]
        )["AvailabilityZones"]
    ]


def get_aws_config() -> Config:
    """Getting the configration required for deployment on AWS.

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
                "choices": vpc_regions_list(),
            }
        ],
        style=styles.second,
    )["region"]

    av_zones = prompt(
        [
            {
                "type": "checkbox",
                "name": "av_zones",
                "message": "Please select atleast two availability zones. (Not sure? Select the first two)",
                "choices": az_list(region),
            }
        ],
        style=styles.second,
    )["av_zones"]

    ## VPC
    cidr_blocks = prompt(
        [
            {
                "type": "input",
                "name": "vpc_cidr_block",
                "message": "Please provide VPC cidr block",
                "default": "10.0.0.0/16",
                # TODO: 'validate': make sure it's a correct ip format
            },
            {
                "type": "input",
                "name": "subnet_cidr_block",
                "message": "Please provide Subnet cidr block",
                "default": "10.0.0.0/24",
                # TODO: 'validate': make sure it's a correct ip format
            },
        ],
        style=styles.second,
    )

    return Config(
        region=region,
        av_zones=av_zones,
        vpc_cidr_block=cidr_blocks["vpc_cidr_block"],
        subnet_cidr_block=cidr_blocks["subnet_cidr_block"],
    )
