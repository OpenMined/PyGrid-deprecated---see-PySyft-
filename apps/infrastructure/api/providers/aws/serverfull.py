from .aws import *


class AWS_Serverfull(AWS):
    def __init__(self, region, av_zones, credentials, app) -> None:
        """
        app (str) : The app("node"/"network") which is to be deployed
        """

        super().__init__(region, av_zones, credentials)

        self.app = app

        self.deploy()

    def deploy(self):
        pass
