from flask import Flask
from .config import Config
#from .config import app
from .config import db
from flask_migrate import Migrate



def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)
    migrate = Migrate(app, db)


    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    @app.route('/')
    def hello_world():
        return 'Howdy!'


    app.add_url_rule('/', endpoint='index')
    return app
