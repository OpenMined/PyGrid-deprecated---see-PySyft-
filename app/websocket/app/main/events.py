"""
This file exists to provide one common place for all websocket events.
"""

from . import hook, local_worker, ws

from .event_routes import *

import json

routes = {
    "get-id": get_node_id,
    "connect-node": connect_grid_nodes,
    "syft-command": syft_command,
    "socket-ping": socket_ping,
    "host-model": host_model,
    "run-inference": run_inference,
    "delete-model": delete_model,
    "list-models": get_models,
    "download-model": download_model,
    "authentication": authentication,
}


def route_requests(message):
    global routes
    if isinstance(message, bytearray):
        return forward_binary_message(message)
    try:
        message = json.loads(message)
        return routes[message["type"]](message)
    except Exception as e:
        print("Exception: ", e)
        return json.dumps({"error": "Invalid JSON format/field!"})


@ws.route("/")
def socket_api(socket):
    while not socket.closed:
        message = socket.receive()
        if not message:
            continue
        else:
            response = route_requests(message)
            if isinstance(response, bytearray):
                socket.send(response, binary=True)
            else:
                socket.send(response)
