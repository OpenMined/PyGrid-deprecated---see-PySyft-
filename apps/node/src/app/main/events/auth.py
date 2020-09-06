from functools import wraps
from json import dumps

from flask import current_app as app
from syft.codes import RESPONSE_MSG
import jwt

from ..core.exceptions import MissingRequestKeyError, InvalidCredentialsError
from ..users import User
from ... import db


def body_token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        response_body = {}

        try:
            message = args[0]
            token = message.get("token")
            if token is None:
                raise MissingRequestKeyError
        except Exception as e:
            status_code = 400  # Bad Request
            response_body[RESPONSE_MSG.ERROR] = str(e)
            return dumps(response_body)

        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms="HS256")
            current_user = User.query.get(data["id"])
        except Exception as e:
            status_code = 403  # Unauthorized
            response_body[RESPONSE_MSG.ERROR] = str(InvalidCredentialsError())
            return dumps(response_body)

        return f(current_user, *args, **kwargs)

    return decorator
