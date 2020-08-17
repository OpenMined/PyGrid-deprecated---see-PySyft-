"""This file exists to provide a route to websocket events."""

from ... import ws
from .socket_handler import SocketHandler
from .common.event_handler import EventHandler

import json

from syft.grid.mockups.requests import RequestResponse
from syft.core.node.domain.domain import Domain
from nacl.signing import SigningKey, VerifyKey

import syft as sy

handler = SocketHandler()

# generate a signing key
signing_key = SigningKey.generate()
verify_key = signing_key.verify_key

OM_domain = Domain(name="OpenMined", root_key=verify_key)
network_handler = EventHandler(OM_domain)


@ws.route("/")
def socket_api(socket):
    """Handle websocket connections and receive their messages.

    Args:
        socket : websocket instance.
    """
    while not socket.closed:
        message = socket.receive()
        if not message:
            continue
        else:
            message = sy.deserialize(blob=message, from_json=True)
            reply = network_handler.process(message)
            if reply:
                socket.send(json.dumps(reply.json()))

    worker_id = handler.remove(socket)


@ws.route("/metadata")
def get_metadata(socket):
    while not socket.closed:
        message = socket.receive()
        if not message:
            continue
        else:
            socket.send(network_handler.node.get_metadata_for_client())
