#!/bin/env python
from app import create_app, socketio
import sys

import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--port", default=8765, type=str, help="port where websocket app will be served."
)

app = create_app(debug=True)

if __name__ == "__main__":
    args = parser.parse_args()
    socketio.run(app, port=args.port)
