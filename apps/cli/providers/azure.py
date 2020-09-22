import subprocess

import click
from PyInquirer import prompt

from ..deploy import base_setup
from ..tf import *
from ..utils import Config, styles
from .provider import *


class AZ:
    def locations_list(self):
        proc = subprocess.Popen(
            "az account list-locations --query '[].{DisplayName:displayName}' --output table",
            shell=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        locations = proc.stdout.read()
        return locations.split("\n")[2:]


class AZURE(Provider):
    """Azure Cloud Provider."""

    def __init__(self, config):
        super().__init__(config)

        self.config.azure = self.get_azure_config()

    def build(self) -> bool:
        pass

    def deploy_network(
        self, apply: bool = True,
    ):
        pass

    def deploy_node(
        self, apply: bool = True,
    ):
        pass

    def get_azure_config(self) -> Config:
        """Getting the configration required for deployment on AZURE.

        Returns:
            Config: Simple Config with the user inputs
        """

        az = AZ()

        location = prompt(
            [
                {
                    "type": "list",
                    "name": "location",
                    "message": "Please select your desired location",
                    "choices": az.locations_list(),
                },
            ],
            style=styles.second,
        )["location"]

        address_space = prompt(
            [
                {
                    "type": "input",
                    "name": "address_space",
                    "message": "Please provide your VPC address_space",
                    "default": "10.0.0.0/16",
                },
            ],
            style=styles.second,
        )["address_space"]

        address_prefix = prompt(
            [
                {
                    "type": "input",
                    "name": "address_prefix",
                    "message": "Please provide subnet address_prefix",
                    "default": "10.0.0.0/24",
                },
            ],
            style=styles.second,
        )["address_prefix"]

        return Config(
            location=location,
            address_space=address_space,
            address_prefix=address_prefix,
        )
