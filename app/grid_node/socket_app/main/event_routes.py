import json
from . import local_worker, hook
import sys

from grid import GridNode


def get_node_id(message):
    return json.dumps({"id": local_worker.id})


def connect_grid_nodes(message):
    worker = GridNode(hook, address=message["address"], id=message["id"])
    return json.dumps({"status": "Succesfully connected."})
