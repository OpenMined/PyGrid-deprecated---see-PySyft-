import click

from ..utils import Config
from .provider import *


class GCP(Provider):
    """Google Cloud Provider."""

    def __init__(self, config):
        super().__init__(config)

        self.config.gcp = self.get_gcp_config()

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

    def get_gcp_config(self) -> Config:
        """Getting the configration required for deployment on GCP.

        Returns:
            Config: Simple Config with the user inputs
        """
        ## TODO:

        return Config()
