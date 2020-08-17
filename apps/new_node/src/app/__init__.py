import logging
import os

from .util import mask_payload_fast
from flask import Flask
from flask_cors import CORS
from flask_executor import Executor
from flask_migrate import Migrate
from flask_sockets import Sockets
from geventwebsocket.websocket import Header

# Monkey patch geventwebsocket.websocket.Header.mask_payload() and
# geventwebsocket.websocket.Header.unmask_payload(), for efficiency
Header.mask_payload = mask_payload_fast
Header.unmask_payload = mask_payload_fast

from .version import __version__

# Default secret key used only for testing / development
DEFAULT_SECRET_KEY = "justasecretkeythatishouldputhere"


def create_app(node_id: str, debug=False, n_replica=None, test_config=None) -> Flask:
    """Create flask application.

    Args:
         node_id: ID used to identify this node.
         debug: debug mode flag.
         n_replica: Number of model replicas used for fault tolerance purposes.
         test_config: database test settings.
    Returns:
         app : Flask App instance.
    """
    app = Flask(__name__)
    app.debug = debug

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", None)

    if app.config["SECRET_KEY"] is None:
        app.config["SECRET_KEY"] = DEFAULT_SECRET_KEY
        logging.warning(
            "Using default secrect key, this is not safe and should be used only for testing and development. To define a secrete key please define the environment variable SECRET_KEY."
        )

    app.config["N_REPLICA"] = n_replica
    sockets = Sockets(app)

    # Register app blueprints
    from .main import ws, http

    sockets.register_blueprint(ws, url_prefix=r"/")
    app.register_blueprint(http, url_prefix=r"/")

    return app
