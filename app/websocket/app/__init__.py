from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from .db_module.models import db

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
        # load the test config if passed in
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db"
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["VERBOSE"] = verbose
    db.init_app(app)
    return app


def create_app(debug=False):
    """Create flask socket-io application."""
    global db
    app = Flask(__name__)
    app.debug = debug
    app.config["SECRET_KEY"] = "justasecretkeythatishouldputhere"

    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)
    CORS(app)

    # Set SQLAlchemy configs
    app = set_database_config(app, test_config=True)
    s = app.app_context().push()
    db.create_all()
    socketio.init_app(app)

    return app
