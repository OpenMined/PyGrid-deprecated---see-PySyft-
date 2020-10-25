import json

import terrascript
import terrascript.data as data  # aws_ami, google_compute_image, ...
import terrascript.provider as provider  # aws, google, ...
import terrascript.resource as resource  # aws_instance, google_compute_instance, ...
from terrascript import Module


class Provider:
    def __init__(self):
        self.tfscript = terrascript.Terrascript()

    def update_script(self):
        with open("main.tf.json", "w") as tfjson:
            json.dump(self.tfscript, tfjson, indent=2, sort_keys=False)
