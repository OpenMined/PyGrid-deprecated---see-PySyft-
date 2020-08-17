from flask import Blueprint

ws = Blueprint(r"ws", __name__)
http = Blueprint(r"http", __name__)

from .io import events, routes
