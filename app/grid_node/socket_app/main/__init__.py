import syft as sy
import torch as th
from flask import Blueprint, current_app


hook = sy.TorchHook(th)
local_worker = sy.VirtualWorker(hook, auto_add=False)


html = Blueprint(r"html", __name__)
ws = Blueprint(r"ws", __name__)


from . import events, routes
from .persistence.models import db
