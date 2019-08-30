from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

# TODO: define a reasonable ping interval
# and ping timeout
PING_INTERVAL = 10000000
PING_TIMEOUT = 5000


socketio = SocketIO(
    async_mode="eventlet", ping_interval=PING_INTERVAL, ping_timeout=PING_TIMEOUT
)


def create_app(debug=False):
    """Create flask socket-io application."""
    app = Flask(__name__)
    app.debug = debug
    app.config["SECRET_KEY"] = "justasecretkeythatishouldputhere"

    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)
    CORS(app)
    socketio.init_app(app)
    return app
