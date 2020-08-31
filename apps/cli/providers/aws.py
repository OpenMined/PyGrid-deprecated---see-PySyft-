import click

from ..utils import Config


def get_aws_config():
    """Getting the configration required for deployment on AWs.

    Returns:
        Config: Simple Config with the user inputs
    """
    region = click.prompt(
        f"Please provide your desired AWS region", default="us-east-1", type=str,
    )
    instance_type = click.prompt(
        f"Please provide your desired AWS instance type", default="t2.micro", type=str,
    )

    ## VPC
    vpc_cidr_block = click.prompt(
        f"Please provide VPC cidr block", default="10.0.0.0/16", type=str,
    )

    ## subnets
    subnet_cidr_block = click.prompt(
        f"Please provide Subnet cidr block", default="10.0.0.0/16", type=str,
    )

    return Config(
        region=region,
        instance_type=instance_type,
        vpc_cidr_block=vpc_cidr_block,
        subnet_cidr_block=subnet_cidr_block,
    )
