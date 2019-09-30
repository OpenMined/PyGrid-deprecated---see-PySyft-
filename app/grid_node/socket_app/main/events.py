import syft as sy
import json

from . import hook, local_worker, ws
from .event_routes import get_node_id, connect_grid_nodes, socket_ping, syft_command
from .persistence.utils import recover_objects, snapshot

routes = {
    "get-id": get_node_id,
    "connect-node": connect_grid_nodes,
    "syft-command": syft_command,
    "socket-ping": socket_ping,
}


def route_requests(message):
    global routes
    try:
        message = json.loads(message)
        return routes[message["type"]](message)
    except Exception as e:
        print(str(e))
        return json.dumps({"error": "Invalid JSON format/field!"})


@ws.route("/")
def socket_api(socket):
    while not socket.closed:
        message = socket.receive()
        if not message:
            continue
        else:
            if isinstance(message, bytearray):
                # Forward syft commands to syft worker

                # Load previous database tensors
                if not local_worker._objects:
                    recover_objects(local_worker)

                decoded_response = local_worker._recv_msg(message)

                # Save local worker state at database
                snapshot(local_worker)

                socket.send(decoded_response, binary=True)
            else:
                socket.send(route_requests(message))
