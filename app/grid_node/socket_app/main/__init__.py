import syft as sy
import torch as th
from flask import Blueprint, current_app


hook = sy.TorchHook(th)
local_worker = hook.local_worker
local_worker.verbose = True
local_worker.is_client_worker = False

html = Blueprint(r"html", __name__)
ws = Blueprint(r"ws", __name__)


def set_node_id(id):
    local_worker.id = id


from . import events, routes
from .persistence.models import db
