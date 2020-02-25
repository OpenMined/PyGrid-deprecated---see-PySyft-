from flask import Blueprint

main = Blueprint("main", __name__)
ws = Blueprint(r"ws", __name__)

from .storage.models import db

from . import routes, events
