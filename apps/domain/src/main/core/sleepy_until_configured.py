from werkzeug.wrappers import Request
from src.main.core.database import SetupConfig
from .database import SetupConfig
from flask import Response
from json import dumps

from .exceptions import AppInSleepyMode
from ..core.codes import RESPONSE_MSG

class SleepyUntilConfigured(object):
    
    def __init__(self, app):
        self.app = app
        self.allowed_routes = ['setup']

    @property
    def is_sleeping(self):
        return SetupConfig.query.first() is not None
    
    def is_route_allowed(self, route):
        return route in self.allowed_routes

    def __call__(self, environ, start_response):
        request = Request(environ)
        mimetype = "application/json"
        response_body = {}
        if self.is_sleeping:
            if self.is_route_allowed(request.path):
                return self.app(environ, start_response)
        else:
            status_code = 400  # Bad Request
            response_body[RESPONSE_MSG.ERROR] = str(AppInSleepyMode())
            return Response(dumps(response_body), status=status_code, mimetype=mimetype)