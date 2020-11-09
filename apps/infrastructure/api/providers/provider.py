import json
import os
import time
from pathlib import Path

import terrascript
import terrascript.data as data
import terrascript.provider as provider
import terrascript.resource as resource
from apps.infrastructure.cli.utils import Config
from terrascript import Module

from ..tf import Terraform
from .utils import *


class Provider:
    def __init__(self, config: Config):
        self._config = config

        self.root_dir = os.path.join(str(Path.home()), ".pygrid", "api")
        os.makedirs(self.root_dir, exist_ok=True)

        self.TF = Terraform()
        self.tfscript = terrascript.Terrascript()

    def deploy(self) -> None:
        if self.config.app.name == "node":
            self.deploy_node()
        elif self.config.app.name == "network":
            self.deploy_network()

        # save the terraform configuration files
        with open(f"{self.root_dir}/main.tf.json", "w") as tfjson:
            json.dump(self.tfscript, tfjson, indent=2, sort_keys=False)

        self.TF.init(self.root_dir)
        self.TF.validate(self.root_dir)

    @property
    def config(self):
        return self._config
