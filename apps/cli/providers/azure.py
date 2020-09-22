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
        ## TODO:

        return Config()
