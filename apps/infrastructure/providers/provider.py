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
        folder_name = f"{config.provider}-{config.app.name}-{config.app.id}"
        dir = os.path.join(str(Path.home()), ".pygrid", "api", folder_name)
        os.makedirs(dir, exist_ok=True)

        self.TF = Terraform(dir)
        self.tfscript = terrascript.Terrascript()

    def deploy(self):
        self.TF.write(self.tfscript)
        try:
            self.TF.init()
            self.TF.validate()
            self.TF.apply()
            output = self.TF.output()
            return (True, output)
        except subprocess.CalledProcessError as err:
            output = {"ERROR": err}
            return (False, output)

    def destroy(self):
        try:
            self.TF.destroy()
            return True
        except subprocess.CalledProcessError as err:
            return False
