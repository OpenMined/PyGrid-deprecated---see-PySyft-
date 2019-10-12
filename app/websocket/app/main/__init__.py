from flask import Blueprint

import syft as sy
import torch as th

# Global variables must be initialized here.
hook = sy.TorchHook(th)
local_worker = sy.VirtualWorker(hook, auto_add=False)
hook.local_worker.is_client_worker = False

html = Blueprint(r"html", __name__)
ws = Blueprint(r"ws", __name__)


from . import routes, events
from .persistence.models import db
from . import auth

# Implement base search locally
# We need this local fix for now to be able run the search operation on Grid
# TODO: remove this after this issue is fixed https://github.com/OpenMined/PySyft/issues/2609

from syft.generic.frameworks.types import FrameworkTensor
