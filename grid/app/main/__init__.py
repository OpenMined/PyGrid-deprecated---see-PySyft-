import syft as sy
import torch as th
from flask import Blueprint

from .. import db, executor
from . import events, routes
from .dfl import auth

# Avoid Pytorch deadlock issues
th.set_num_threads(1)

hook = sy.TorchHook(th)
local_worker = sy.VirtualWorker(hook, auto_add=False)
hook.local_worker.is_client_worker = False

main = Blueprint("main", __name__)
ws = Blueprint(r"ws", __name__)
