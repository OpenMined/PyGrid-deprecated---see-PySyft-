import logging
from secrets import token_hex
from json import dumps, loads
from json.decoder import JSONDecodeError
from datetime import datetime, timedelta

import jwt
from bcrypt import hashpw, checkpw, gensalt
from syft.codes import RESPONSE_MSG
from flask import request, Response
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash

from ..core.exceptions import (
    PyGridError,
    UserNotFoundError,
    RoleNotFoundError,
    GroupNotFoundError,
    AuthorizationError,
    MissingRequestKeyError,
    InvalidCredentialsError,
)
from ... import db
from .. import main_routes
from ..users import Role, User, UserGroup, Group
from ..users.user_ops import (
    signup_user,
    login_user,
    get_all_users,
    get_specific_user,
    put_email,
    put_role,
    put_password,
    put_groups,
    delete_user,
    search_users
)
from .auth import token_required


def model_to_json(model):
    """Returns a JSON representation of an SQLAlchemy-backed object."""
    json = {}
    for col in model.__mapper__.attrs.keys():
        if col != "hashed_password" and col != "salt":
            json[col] = getattr(model, col)

    return json


def expand_user_object(user):
    def get_group(usr_group):
        query = db.session().query
        group = usr_group.group
        group = query(Group).get(group)
        group = model_to_json(group)
        return group

    query = db.session().query
    user = model_to_json(user)
    user["role"] = query(Role).get(user["role"])
    user["role"] = model_to_json(user["role"])
    user["groups"] = query(UserGroup).filter_by(user=user["id"]).all()
    user["groups"] = [get_group(usr_group) for usr_group in user["groups"]]

    return user


def salt_and_hash_password(password, rounds):
    password = password.encode("UTF-8")
    salt = gensalt(rounds=rounds)
    hashed = hashpw(password, salt)
    hashed = hashed[len(salt) :]
    hashed = hashed.decode("UTF-8")
    salt = salt.decode("UTF-8")
    return salt, hashed


def identify_user(private_key):
    if private_key is None:
        raise MissingRequestKeyError

    usr = db.session.query(User).filter_by(private_key=private_key).one_or_none()
    if usr is None:
        raise UserNotFoundError

    usr_role = db.session.query(Role).get(usr.role)
    if usr_role is None:
        raise RoleNotFoundError

    return usr, usr_role


@main_routes.route("/users", methods=["POST"])
def signup_user_route():
    status_code = 200  # Success
    response_body = {}
    private_key = usr = usr_role = None

    try:
        private_key = request.headers.get("private-key")
        data = loads(request.data)
        password = data.get("password")
        email = data.get("email")
        role = data.get("role")

        if email is None or password is None:
            raise MissingRequestKeyError
        
        user = signup_user(private_key, email, password, role)
        user = expand_user_object(user)
        response_body = {RESPONSE_MSG.SUCCESS: True, "user": user}

    except RoleNotFoundError as e:
        status_code = 404  # Resource not found
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User not found in post-role", exc_info=e)
    except (InvalidCredentialsError, AuthorizationError) as e:
        status_code = 403  # Unathorized
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User credentials are invalid", exc_info=e)
    except (TypeError, MissingRequestKeyError, PyGridError, JSONDecodeError) as e:
        status_code = 400  # Bad Request
        response_body[RESPONSE_MSG.ERROR] = str(e)
    except Exception as e:
        status_code = 500  # Internal Server Error
        response_body[RESPONSE_MSG.ERROR] = str(e)

    return Response(
        dumps(response_body), status=status_code, mimetype="application/json"
    )


@main_routes.route("/users/login", methods=["POST"])
def login_user_route():
    status_code = 200  # Success
    response_body = {}

    try:

        data = loads(request.data)
        email = data.get("email")
        password = data.get("password")
        private_key = request.headers.get("private-key")
        
        if email is None or password is None or private_key is None:
            raise MissingRequestKeyError

        token = login_user(email, password)
        response_body = {RESPONSE_MSG.SUCCESS: True, "token": token}

    except InvalidCredentialsError as e:
        status_code = 403  # Unathorized
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User credentials are invalid", exc_info=e)
    except (RoleNotFoundError, UserNotFoundError) as e:
        status_code = 404  # Resource not found
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User not found in post-role", exc_info=e)
    except (TypeError, MissingRequestKeyError, PyGridError, JSONDecodeError) as e:
        status_code = 400  # Bad Request
        response_body[RESPONSE_MSG.ERROR] = str(e)
    except Exception as e:
        status_code = 500  # Internal Server Error
        response_body[RESPONSE_MSG.ERROR] = str(e)

    return Response(
        dumps(response_body), status=status_code, mimetype="application/json"
    )


@main_routes.route("/users", methods=["GET"])
@token_required
def get_all_users_route(current_user):
    status_code = 200  # Success
    response_body = {}

    try:
        private_key = request.headers.get("private-key")
        if private_key is None:
            raise MissingRequestKeyError

        if private_key != current_user.private_key:
            raise InvalidCredentialsError

        users = get_all_users(current_user, private_key)
        users = [expand_user_object(user) for user in users]
        response_body = {RESPONSE_MSG.SUCCESS: True, "users": users}

    except (InvalidCredentialsError, AuthorizationError) as e:
        status_code = 403  # Unathorized
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User credentials are invalid", exc_info=e)
    except (RoleNotFoundError, UserNotFoundError) as e:
        status_code = 404  # Resource not found
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User not found in get-roles", exc_info=e)
    except (TypeError, MissingRequestKeyError, PyGridError, JSONDecodeError) as e:
        status_code = 400  # Bad Request
        response_body[RESPONSE_MSG.ERROR] = str(e)
    except Exception as e:
        status_code = 500  # Internal Server Error
        response_body[RESPONSE_MSG.ERROR] = str(e)

    return Response(
        dumps(response_body), status=status_code, mimetype="application/json"
    )


@main_routes.route("/users/<user_id>", methods=["GET"])
@token_required
def get_specific_user_route(current_user, user_id):
    status_code = 200  # Success
    response_body = {}

    try:
        user_id = int(user_id)
        private_key = request.headers.get("private-key")
        if private_key is None:
            raise MissingRequestKeyError

        if private_key != current_user.private_key:
            raise InvalidCredentialsError

        user = get_specific_user(current_user, private_key, user_id)
        user = expand_user_object(user)
        response_body = {RESPONSE_MSG.SUCCESS: True, "user": user}

    except (InvalidCredentialsError, AuthorizationError) as e:
        status_code = 403  # Unathorized
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User credentials are invalid", exc_info=e)
    except (RoleNotFoundError, UserNotFoundError) as e:
        status_code = 404  # Resource not found
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User not found in get-roles", exc_info=e)
    except (TypeError, MissingRequestKeyError, PyGridError, JSONDecodeError) as e:
        status_code = 400  # Bad Request
        response_body[RESPONSE_MSG.ERROR] = str(e)
    except Exception as e:
        status_code = 500  # Internal Server Error
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User credentials are invalid", exc_info=e)

    return Response(
        dumps(response_body), status=status_code, mimetype="application/json"
    )


@main_routes.route("/users/<user_id>/email", methods=["PUT"])
@token_required
def put_email_route(current_user, user_id):
    status_code = 200  # Success
    response_body = {}

    try:
        user_id = int(user_id)
        data = loads(request.data)
        email = data.get("email")
        private_key = request.headers.get("private-key")

        if email is None or private_key is None:
            raise MissingRequestKeyError
        if private_key != current_user.private_key:
            raise InvalidCredentialsError

        user = put_email(current_user, private_key, email, user_id)
        user = expand_user_object(user)
        response_body = {RESPONSE_MSG.SUCCESS: True, "user": user}

    except (InvalidCredentialsError, AuthorizationError) as e:
        status_code = 403  # Unathorized
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User not authorized to post-role", exc_info=e)
    except (RoleNotFoundError, UserNotFoundError) as e:
        status_code = 404  # Resource not found
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User/Role not found in put-role", exc_info=e)
    except (TypeError, MissingRequestKeyError, PyGridError, JSONDecodeError) as e:
        status_code = 400  # Bad Request
        response_body[RESPONSE_MSG.ERROR] = str(e)
    except Exception as e:
        status_code = 500  # Internal Server Error
        response_body[RESPONSE_MSG.ERROR] = str(e)

    return Response(
        dumps(response_body), status=status_code, mimetype="application/json"
    )


@main_routes.route("/users/<user_id>/role", methods=["PUT"])
@token_required
def put_role_route(current_user, user_id):
    status_code = 200  # Success
    response_body = {}

    try:
        user_id = int(user_id)
        data = loads(request.data)
        role = data.get("role")
        private_key = request.headers.get("private-key")

        if role is None or private_key is None:
            raise MissingRequestKeyError
        if private_key != current_user.private_key:
            raise InvalidCredentialsError

        edited_user = put_role(current_user, private_key, role, user_id)
        edited_user = expand_user_object(edited_user)
        response_body = {RESPONSE_MSG.SUCCESS: True, "user": edited_user}

    except (InvalidCredentialsError, AuthorizationError) as e:
        status_code = 403  # Unathorized
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User not authorized to post-role", exc_info=e)
    except (RoleNotFoundError, UserNotFoundError) as e:
        status_code = 404  # Resource not found
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User/Role not found in put-role", exc_info=e)
    except (TypeError, MissingRequestKeyError, PyGridError, JSONDecodeError) as e:
        status_code = 400  # Bad Request
        response_body[RESPONSE_MSG.ERROR] = str(e)
    except Exception as e:
        status_code = 500  # Internal Server Error
        response_body[RESPONSE_MSG.ERROR] = str(e)

    return Response(
        dumps(response_body), status=status_code, mimetype="application/json"
    )


@main_routes.route("/users/<user_id>/password", methods=["PUT"])
@token_required
def put_password_role(current_user, user_id):
    status_code = 200  # Success
    response_body = {}

    try:
        user_id = int(user_id)
        data = loads(request.data)
        password = data.get("password")
        private_key = request.headers.get("private-key")

        if password is None or private_key is None:
            raise MissingRequestKeyError
        if private_key != current_user.private_key:
            raise InvalidCredentialsError

        edited_user = put_password(current_user, private_key,
                                   password, user_id)
        edited_user = expand_user_object(edited_user)

        response_body = {RESPONSE_MSG.SUCCESS: True, "user": edited_user}

    except (InvalidCredentialsError, AuthorizationError) as e:
        status_code = 403  # Unathorized
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User not authorized to post-role", exc_info=e)
    except (RoleNotFoundError, UserNotFoundError) as e:
        status_code = 404  # Resource not found
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User/Role not found in put-role", exc_info=e)
    except (TypeError, MissingRequestKeyError, PyGridError, JSONDecodeError) as e:
        status_code = 400  # Bad Request
        response_body[RESPONSE_MSG.ERROR] = str(e)
    except Exception as e:
        status_code = 500  # Internal Server Error
        response_body[RESPONSE_MSG.ERROR] = str(e)

    return Response(
        dumps(response_body), status=status_code, mimetype="application/json"
    )


@main_routes.route("/users/<user_id>/groups", methods=["PUT"])
@token_required
def put_groups_route(current_user, user_id):
    status_code = 200  # Success
    response_body = {}

    try:
        user_id = int(user_id)
        data = loads(request.data)
        groups = data.get("groups")
        private_key = request.headers.get("private-key")

        if groups is None or private_key is None:
            raise MissingRequestKeyError
        if private_key != current_user.private_key:
            raise InvalidCredentialsError
        
        edited_user = put_groups(current_user, private_key, groups, user_id)
        edited_user = expand_user_object(edited_user)
        response_body = {RESPONSE_MSG.SUCCESS: True, "user": edited_user}

    except (InvalidCredentialsError, AuthorizationError) as e:
        status_code = 403  # Unathorized
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User not authorized to post-role", exc_info=e)
    except (GroupNotFoundError, RoleNotFoundError, UserNotFoundError) as e:
        status_code = 404  # Resource not found
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User/Role not found in put-role", exc_info=e)
    except (TypeError, MissingRequestKeyError, PyGridError, JSONDecodeError) as e:
        status_code = 400  # Bad Request
        response_body[RESPONSE_MSG.ERROR] = str(e)
    except Exception as e:
        status_code = 500  # Internal Server Error
        response_body[RESPONSE_MSG.ERROR] = str(e)

    return Response(
        dumps(response_body), status=status_code, mimetype="application/json"
    )


@main_routes.route("/users/<user_id>", methods=["DELETE"])
@token_required
def delete_user_role(current_user, user_id):
    status_code = 200  # Success
    response_body = {}

    try:
        user_id = int(user_id)
        private_key = request.headers.get("private-key")

        if private_key is None:
            raise MissingRequestKeyError
        if private_key != current_user.private_key:
            raise InvalidCredentialsError
        
        edited_user = delete_user(current_user, private_key, user_id)
        edited_user = expand_user_object(edited_user)
        response_body = {RESPONSE_MSG.SUCCESS: True, "user": edited_user}

    except (InvalidCredentialsError, AuthorizationError) as e:
        status_code = 403  # Unathorized
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User not authorized to post-role", exc_info=e)
    except (GroupNotFoundError, RoleNotFoundError, UserNotFoundError) as e:
        status_code = 404  # Resource not found
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User/Role not found in put-role", exc_info=e)
    except (TypeError, MissingRequestKeyError, PyGridError, JSONDecodeError) as e:
        status_code = 400  # Bad Request
        response_body[RESPONSE_MSG.ERROR] = str(e)
    except Exception as e:
        status_code = 500  # Internal Server Error
        response_body[RESPONSE_MSG.ERROR] = str(e)

    return Response(
        dumps(response_body), status=status_code, mimetype="application/json"
    )


@main_routes.route("/users/search", methods=["POST"])
@token_required
def search_users_route(current_user):
    status_code = 200  # Success
    response_body = {}

    try:
        filters = loads(request.data)
        email = filters.get("email")
        role = filters.get("role")
        group = filters.get("group")

        private_key = request.headers.get("private-key")

        if email is None and role is None and group is None:
            raise MissingRequestKeyError
        if private_key is None:
            raise MissingRequestKeyError
        if private_key != current_user.private_key:
            raise InvalidCredentialsError

        users = search_users(current_user, private_key, filters, group) 
        users = [expand_user_object(user) for user in users]
        response_body = {RESPONSE_MSG.SUCCESS: True, "users": users}

    except (InvalidCredentialsError, AuthorizationError) as e:
        status_code = 403  # Unathorized
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User not authorized to post-role", exc_info=e)
    except (GroupNotFoundError, RoleNotFoundError, UserNotFoundError) as e:
        status_code = 404  # Resource not found
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User/Role not found in put-role", exc_info=e)
    except (TypeError, MissingRequestKeyError, PyGridError, JSONDecodeError) as e:
        status_code = 400  # Bad Request
        response_body[RESPONSE_MSG.ERROR] = str(e)
    except Exception as e:
        status_code = 500  # Internal Server Error
        response_body[RESPONSE_MSG.ERROR] = str(e)

    return Response(
        dumps(response_body), status=status_code, mimetype="application/json"
    )
