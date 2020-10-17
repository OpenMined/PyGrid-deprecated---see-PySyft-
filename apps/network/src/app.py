"""CODING GUIDELINES:

- Add docstrings following the pattern chosen by the community.
- Add comments explaining step by step how your method works and the purpose of it.
- If possible, add examples showing how to call them properly.
- Remember to add the parameters and return types.
- Add unit tests / integration tests for every feature that you develop in order to cover at least 80% of the code.
- Import order : python std libraries, extendend libs, internal source code.
"""

# Std Python imports
from typing import Optional
import logging
import os

# Extended Python imports
from flask import Flask
from flask_migrate import Migrate
from flask_sockets import Sockets
from geventwebsocket.websocket import Header
from sqlalchemy_utils.functions import database_exists

# Internal imports
from main.utils.monkey_patch import mask_payload_fast
from main.routes import (
    roles_blueprint,
    users_blueprint,
    setup_blueprint,
    association_requests_blueprint,
    infrastructure_blueprint,
)

import config

db = SQLAlchemy()
DEFAULT_SECRET_KEY = "justasecretkeythatishouldputhere"

# Masking/Unmasking is a process used to guarantee some level of security
# during the transportation of the messages across proxies (as described in WebSocket RFC).
# Since the masking process needs to iterate over the message payload,
# the larger this message is, the longer it takes to process it.
# The flask_sockets / gevent-websocket developed this process using only native language structures.
# Replacing these structures for NumPy structures should increase the performance.
Header.mask_payload = mask_payload_fast
Header.unmask_payload = mask_payload_fast

# Setup log
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s]: {} %(levelname)s %(message)s".format(os.getpid()),
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger()


def set_database_config(app, db_config=None, verbose=False):
    """Set configs to use SQL Alchemy library.

    Args:
        app: Flask application.
        db_config : Dictionary containing SQLAlchemy configs for test purposes.
        verbose : Level of flask application verbosity.

    Returns:
        app: Flask application.

    Raises:
        RuntimeError : If DATABASE_URL or db_config didn't initialize, RuntimeError exception will be raised.
    """
    db_url = os.environ.get("DATABASE_URL")
    migrate = Migrate(app, db)
    if db_config is None:
        if db_url:
            app.config.from_mapping(
                SQLALCHEMY_DATABASE_URI=db_url, SQLALCHEMY_TRACK_MODIFICATIONS=False
            )
        else:
            raise RuntimeError(
                "Invalid database address: Set DATABASE_URL environment var or add db_config parameter at create_app method."
            )
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = db_config["SQLALCHEMY_DATABASE_URI"]
        app.config["TESTING"] = (
            db_config["TESTING"] if db_config.get("TESTING") else True
        )
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = (
            db_config["SQLALCHEMY_TRACK_MODIFICATIONS"]
            if db_config.get("SQLALCHEMY_TRACK_MODIFICATIONS")
            else False
        )
    app.config["VERBOSE"] = verbose
    db.init_app(app)


def seed_db():
    """Adds Administrator and Owner Roles to database."""
    global db
    new_user = Role(
        name="Administrator",
        can_edit_settings=False,
        can_create_users=False,
        can_edit_roles=False,
        can_manage_nodes=False,
    )
    db.session.add(new_user)
    new_user = Role(
        name="Owner",
        can_edit_settings=True,
        can_create_users=True,
        can_edit_roles=True,
        can_manage_nodes=True,
    )
    db.session.add(new_user)

    db.session.commit()


def create_app(debug=False, secret_key=DEFAULT_SECRET_KEY) -> Flask:
    """This method creates a new Flask App instance and attach it with some
    HTTP/Websocket bluetprints.

    PS: In order to keep modularity and reause, do not add any PyGrid logic here, this method should be as logic agnostic as possible.
    :return: returns a Flask app instance.
    :rtype: Flask
    """
    logger.info(f"Starting app in {config.APP_ENV} environment")

    # Create Flask app instance
    app = Flask(__name__)

    app.config.from_object("config")

    # Bind websocket in Flask app instance
    sockets = Sockets(app)

    # Register HTTP blueprints
    # Here you should add all the blueprints related to HTTP routes.
    app.register_blueprint(roles_blueprint, url_prefix=r"/roles/")
    app.register_blueprint(users_blueprint, url_prefix=r"/users/")
    app.register_blueprint(setup_blueprint, url_prefix=r"/setup/")
    app.register_blueprint(infrastructure_blueprint, url_prefix=r"/networks/")
    app.register_blueprint(
        association_requests_blueprint, url_prefix=r"/association-requests/"
    )

    # Register WebSocket blueprints
    # Here you should add all the blueprints related to WebSocket routes.
    # sockets.register_blueprint()


    app.debug = debug
    app.config["SECRET_KEY"] = secret_key

    # Set SQLAlchemy configs
    global db
    set_database_config(app, db_config=db_config)
    s = app.app_context().push()

    if database_exists(db.engine.url):
        db.create_all()
    else:
        db.create_all()
        seed_db()

    db.session.commit()

    # Send app instance
    return app
