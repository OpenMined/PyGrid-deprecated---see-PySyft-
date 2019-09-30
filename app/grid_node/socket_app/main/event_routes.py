import json
from . import local_worker, hook
import syft as sy
import torch as th

from grid import GridNode


def get_node_id(message):
    return json.dumps({"id": local_worker.id})


def connect_grid_nodes(message):
    worker = GridNode(hook, address=message["address"], id=message["id"])
    return json.dumps({"status": "Succesfully connected."})


def socket_ping(message):
    return json.dumps({"alive": "True"})


def syft_command(message):
    print("\n\n\nMessage: ", message, "\n\n\n")
    content = sy.serde.deserialize(message["payload"])
    response = local_worker._message_router[message["msg_type"]](message["content"])
    payload = sy.serde.serialize(response, force_no_serialization=True)
    return json.dumps({"type": "command-response", "response": payload})
