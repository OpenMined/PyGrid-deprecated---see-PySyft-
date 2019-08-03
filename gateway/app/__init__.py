from flask import Flask
from flask_cors import CORS


def create_app(debug=False):
    """Create flask application."""
    app = Flask(__name__)
    app.debug = debug
    app.config["SECRET_KEY"] = "justasecretkeythatishouldputhere"

    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)
    CORS(app)
    return app
