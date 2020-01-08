"""
This file exists to provide a route to websocket events.
"""

from .. import ws

import json

# Websocket events routes
# This structure allows compatibility between javascript applications (syft.js/grid.js) and PyGrid.
routes = {}


def route_requests(message):
    """ Handle a message from websocket connection and route them to the desired method.

        Args:
            message : message received.
        Returns:
            message_response : message response.
    """
    global routes
    if isinstance(message, bytearray):
        return forward_binary_message(message)
    try:
        message = json.loads(message)
        return routes[message[REQUEST_MSG.TYPE_FIELD]](message)
    except Exception as e:
        return json.dumps({"error": "Invalid JSON format/field!"})


@ws.route("/")
def socket_api(socket):
    """ Handle websocket connections and receive their messages.
    
        Args:
            socket : websocket instance.
    """
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
