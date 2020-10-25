import json
import time
from pathlib import Path

import terrascript
import terrascript.data as data  # aws_ami, google_compute_image, ...
import terrascript.provider as provider  # aws, google, ...
import terrascript.resource as resource  # aws_instance, google_compute_instance, ...
from terrascript import Module

from ..tf import TF


class Provider:
    def __init__(self):
        self.tfscript = terrascript.Terrascript()

    def deploy(self):
        # write file
        with open(
            f"{str(Path.home() / '.pygrid/')}/main_{time.strftime('%Y-%m-%d_%H%M%S')}.tf.json",
            "w",
        ) as tfjson:
            json.dump(self.tfscript, tfjson, indent=2, sort_keys=False)

        TF.init()
        TF.apply()
