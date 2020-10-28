import json
import time
from pathlib import Path

import terrascript
import terrascript.data as data
import terrascript.provider as provider
import terrascript.resource as resource
from terrascript import Module

from ..tf import TF


class Provider:
    def __init__(self):
        self.tfscript = terrascript.Terrascript()

    def deploy(self):
        # save the terraform configuration as a file
        with open(
            f"{str(Path.home() / '.pygrid/')}/main_{time.strftime('%Y-%m-%d_%H%M%S')}.tf.json",
            "w",
        ) as tfjson:
            json.dump(self.tfscript, tfjson, indent=2, sort_keys=False)

        TF.init()
        TF.apply()
