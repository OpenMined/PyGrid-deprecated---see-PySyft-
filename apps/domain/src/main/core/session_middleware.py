# third party
from flask import Response
from flask import current_app as app
import jwt
from werkzeug.wrappers import Request

# grid relative
from ..core.database import User
from .database import db


class SessionMiddleware(object):
    def __init__(self, app, app_wsgi):
        self.app = app
        self.wsgi = app_wsgi

    def __call__(self, environ, start_response):
        request = Request(environ)
        response_body = {}

        with self.app.app_context():
            current_user = None
            token = request.headers.get("token", None)
            if token:
                data = jwt.decode(token, app.config["SECRET_KEY"], algorithms="HS256")
                current_user = db.session.query(User).get(data["id"])

        environ["current_user"] = current_user
        return self.wsgi(environ, start_response)
