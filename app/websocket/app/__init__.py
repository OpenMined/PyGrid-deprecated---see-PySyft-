from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

socketio = SocketIO(async_mode="eventlet")


def set_database_config(app, test_config=None, verbose=False):
    global db
    db_url = os.environ.get("DATABASE_URL")
    migrate = Migrate(app, db)
    if test_config is None:
        app.config.from_mapping(
            SQLALCHEMY_DATABASE_URI=db_url, SQLALCHEMY_TRACK_MODIFICATIONS=False
        )

    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = test_config["SQLALCHEMY_DATABASE_URI"]
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["VERBOSE"] = verbose
    db.init_app(app)
    return app


def create_app(debug=False, tst_config=None):
    """Create flask socket-io application."""
    app = Flask(__name__)
    app.debug = debug
    app.config["SECRET_KEY"] = "justasecretkeythatishouldputhere"

    from .main import main as main_blueprint
    from .main import db

    global db

    app.register_blueprint(main_blueprint)
    CORS(app)

    # Set SQLAlchemy configs
    app = set_database_config(app, test_config=tst_config)
    s = app.app_context().push()
    db.create_all()
    socketio.init_app(app)

    return app
