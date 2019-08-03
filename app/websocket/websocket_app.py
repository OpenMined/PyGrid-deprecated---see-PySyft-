#!/bin/env python
"""
    Grid Node is a Socket/HTTP server used to manage / compute data remotely
"""

from app import create_app, socketio
import sys
import requests
import json
import os

# These environment variables must be set before starting the application.
gateway_url = os.environ["GRID_NETWORK_URL"]
node_id = os.environ["ID"]
node_address = os.environ["ADDRESS"]
port = os.environ["PORT"]


app = create_app(debug=False)

if __name__ == "__main__":
    # Register request
    requests.post(
        gateway_url + "/join",
        data=json.dumps({"node-id": node_id, "node-address": node_address}),
    )
    socketio.run(app, host="0.0.0.0", port=port)
