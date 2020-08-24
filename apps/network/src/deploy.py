"""This package set up the app and server."""

import json
import os

from flask import Blueprint, Flask, Response
from flask_lambda import FlaskLambda
from flask_migrate import Migrate
from flask_sockets import Sockets
from flask_sqlalchemy import SQLAlchemy
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from sqlalchemy_utils.functions import database_exists

# Set routes/events
ws = Blueprint(r"ws", __name__)
http = Blueprint(r"http", __name__)
# Set db client instance
db = SQLAlchemy()


DEFAULT_SECRET_KEY = "justasecretkeythatishouldputhere"
__version__ = "0.1.0"


# Add a test route
@http.route("/test-deployment/")
def test():
    return Response(
        json.dumps({"message": "Serverless deployment successful."}),
        status=200,
        mimetype="application/json",
    )


def create_lambda_app(secret_key=DEFAULT_SECRET_KEY, db_config=None) -> FlaskLambda:
    """Create Flask Lambda app.

    Args:
        secret_key (str): Secret key application
        db_config (Union[None, dict]): Database configuration

    Returns:
        app (Flask): flask application
    """
    app = FlaskLambda(__name__)
    app.debug = False
    app.config["SECRET_KEY"] = secret_key

    # Global socket handler
    sockets = Sockets(app)

    app.register_blueprint(http, url_prefix=r"/")
    sockets.register_blueprint(ws, url_prefix=r"/")

    # Set SQLAlchemy configs
    # global db
    # set_database_config(app, db_config=db_config)
    # s = app.app_context().push()
    #
    # if database_exists(db.engine.url):
    #     db.create_all()
    # else:
    #     db.create_all()
    #     seed_db()
    #
    # db.session.commit()

    return app


app = create_lambda_app()
