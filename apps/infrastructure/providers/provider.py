import json
import os
import subprocess
import time
from pathlib import Path

import terrascript
import terrascript.data as data
import terrascript.provider as provider
import terrascript.resource as resource
from terrascript import Module

from apps.infrastructure.tf import Terraform
from apps.infrastructure.utils import Config


class Provider:
    def __init__(self, config):
        self.app_dir = os.path.join(
            str(Path.home()), ".pygrid", "api", config.app, config.id
        )
        os.makedirs(self.app_dir, exist_ok=True)

        self.TF = Terraform()
        self.tfscript = terrascript.Terrascript()

    def deploy(self):
        # save the terraform configuration files
        with open(f"{self.app_dir}/main.tf.json", "w") as tfjson:
            json.dump(self.tfscript, tfjson, indent=2, sort_keys=False)

        try:
            self.TF.init(self.app_dir)
            self.TF.validate(self.app_dir)
            self.TF.apply(self.app_dir)
            output = self.TF.output(self.app_dir)
            return (True, output)
        except subprocess.CalledProcessError as err:
            output = {"ERROR": err}
            return (False, output)

    def destroy(self):
        try:
            self.TF.destroy(self.app_dir)
            return True
        except subprocess.CalledProcessError as err:
            return False
