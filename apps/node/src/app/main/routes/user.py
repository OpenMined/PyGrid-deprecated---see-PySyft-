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
def signup_user():
    status_code = 200  # Success
    response_body = {}
    usr_role = None
    usr = None

    try:
        private_key = request.headers.get("private-key")
        if private_key is not None:
            usr, usr_role = identify_user(private_key)
    except Exception as e:
        logging.warning("Existing user could not be linked")

    try:

        if private_key is not None and (usr is None or usr_role is None):
            raise InvalidCredentialsError
        data = loads(request.data)
        password = data.get("password")
        email = data.get("email")
        role = data.get("role")

        if email is None or password is None:
            raise MissingRequestKeyError

        private_key = token_hex(32)
        salt, hashed = salt_and_hash_password(password, 12)
        no_user = len(db.session.query(User).all()) == 0

        if no_user:
            role = db.session.query(Role.id).filter_by(name="Owner").first()
            if role is None:
                raise RoleNotFoundError
            role = role[0]
            new_user = User(
                email=email,
                hashed_password=hashed,
                salt=salt,
                private_key=private_key,
                role=role,
            )
        elif role is not None and usr_role is not None and usr_role.can_create_users:
            if db.session.query(Role).get(role) is None:
                raise RoleNotFoundError
            new_user = User(
                email=email,
                hashed_password=hashed,
                salt=salt,
                private_key=private_key,
                role=role,
            )
        else:
            role = db.session.query(Role.id).filter_by(name="User").first()
            if role is None:
                raise RoleNotFoundError
            role = role[0]
            new_user = User(
                email=email,
                hashed_password=hashed,
                salt=salt,
                private_key=private_key,
                role=role,
            )

        db.session.add(new_user)
        db.session.commit()

        user = model_to_json(new_user)
        user["role"] = db.session.query(Role).get(user["role"])
        user["role"] = model_to_json(user["role"])
        user.pop("hashed_password", None)
        user.pop("salt", None)

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


# LOGIN USER


@main_routes.route("/users/login", methods=["POST"])
def login_user():
    status_code = 200  # Success
    response_body = {}

    try:

        data = loads(request.data)
        email = data.get("email")
        password = data.get("password")
        if email is None or password is None:
            raise MissingRequestKeyError

        password = password.encode("UTF-8")
        private_key = request.headers.get("private-key")
        if private_key is None:
            raise MissingRequestKeyError

        usr = User.query.filter_by(email=email, private_key=private_key).first()
        if usr is None:
            raise InvalidCredentialsError

        hashed = usr.hashed_password.encode("UTF-8")
        salt = usr.salt.encode("UTF-8")

        if checkpw(password, salt + hashed):
            token = jwt.encode({"id": usr.id}, app.config["SECRET_KEY"])
            response_body = {RESPONSE_MSG.SUCCESS: True, "token": token.decode("UTF-8")}
        else:
            raise InvalidCredentialsError

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
def get_all_users(current_user):
    status_code = 200  # Success
    response_body = {}

    try:
        private_key = request.headers.get("private-key")
        if private_key is None:
            raise MissingRequestKeyError

        if private_key != current_user.private_key:
            raise InvalidCredentialsError

        usr_role = Role.query.get(current_user.role)
        if usr_role is None:
            raise RoleNotFoundError

        if not usr_role.can_triage_jobs:
            raise AuthorizationError

        users = [expand_user_object(user) for user in User.query.all()]

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


@main_routes.route("/users/<id>", methods=["GET"])
@token_required
def get_specific_user(current_user, id):
    status_code = 200  # Success
    response_body = {}

    try:
        private_key = request.headers.get("private-key")
        if private_key is None:
            raise MissingRequestKeyError

        if private_key != current_user.private_key:
            raise InvalidCredentialsError

        usr_role = Role.query.get(current_user.role)
        if usr_role is None:
            raise RoleNotFoundError

        if not usr_role.can_triage_jobs:
            raise AuthorizationError

        user = User.query.get(id)
        if user is None:
            raise UserNotFoundError

        response_body = {RESPONSE_MSG.SUCCESS: True, "user": expand_user_object(user)}

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


@main_routes.route("/users/<id>/email", methods=["PUT"])
@token_required
def put_email(current_user, id):
    status_code = 200  # Success
    response_body = {}

    try:

        data = loads(request.data)
        email = data.get("email")
        private_key = request.headers.get("private-key")
        usr_role = db.session.query(Role).get(current_user.role)
        edited_user = db.session.query(User).get(id)

        if email is None or private_key is None:
            raise MissingRequestKeyError
        if private_key != current_user.private_key:
            raise InvalidCredentialsError
        if usr_role is None:
            raise RoleNotFoundError
        if int(id) != current_user.id and not usr_role.can_create_users:
            raise AuthorizationError
        if edited_user is None:
            raise UserNotFoundError

        setattr(edited_user, "email", email)
        db.session.commit()

        response_body = {
            RESPONSE_MSG.SUCCESS: True,
            "user": expand_user_object(edited_user),
        }

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


@main_routes.route("/users/<id>/role", methods=["PUT"])
@token_required
def put_role(current_user, id):
    status_code = 200  # Success
    response_body = {}

    try:
        if int(id) == 1:  # can't change Owner
            raise AuthorizationError

        data = loads(request.data)
        role = data.get("role")
        private_key = request.headers.get("private-key")
        usr_role = db.session.query(Role).get(current_user.role)
        owner_role = db.session.query(User).get(1).id
        edited_user = db.session.query(User).get(id)

        if role is None or private_key is None:
            raise MissingRequestKeyError
        if private_key != current_user.private_key:
            raise InvalidCredentialsError
        if usr_role is None:
            raise RoleNotFoundError
        if int(id) != current_user.id and not usr_role.can_create_users:
            raise AuthorizationError
        # Only Owners can create other Owners
        if role == owner_role and current_user.id != owner_role:
            raise AuthorizationError
        if edited_user is None:
            raise UserNotFoundError

        setattr(edited_user, "role", int(role))
        db.session.commit()

        response_body = {
            RESPONSE_MSG.SUCCESS: True,
            "user": expand_user_object(edited_user),
        }

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


@main_routes.route("/users/<id>/password", methods=["PUT"])
@token_required
def put_password(current_user, id):
    status_code = 200  # Success
    response_body = {}

    try:

        data = loads(request.data)
        password = data.get("password")
        private_key = request.headers.get("private-key")
        usr_role = db.session.query(Role).get(current_user.role)
        edited_user = db.session.query(User).get(id)

        if password is None or private_key is None:
            raise MissingRequestKeyError
        if private_key != current_user.private_key:
            raise InvalidCredentialsError
        if usr_role is None:
            raise RoleNotFoundError
        if int(id) != current_user.id and not usr_role.can_create_users:
            raise AuthorizationError
        if edited_user is None:
            raise UserNotFoundError

        salt, hashed = salt_and_hash_password(password, 12)
        setattr(edited_user, "salt", salt)
        setattr(edited_user, "hashed_password", hashed)
        db.session.commit()

        response_body = {
            RESPONSE_MSG.SUCCESS: True,
            "user": expand_user_object(edited_user),
        }

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


@main_routes.route("/users/<id>/groups", methods=["PUT"])
@token_required
def put_groups(current_user, id):
    status_code = 200  # Success
    response_body = {}

    try:

        data = loads(request.data)
        groups = data.get("groups")
        private_key = request.headers.get("private-key")
        usr_role = db.session.query(Role).get(current_user.role)
        edited_user = db.session.query(User).get(id)

        if groups is None or private_key is None:
            raise MissingRequestKeyError
        if private_key != current_user.private_key:
            raise InvalidCredentialsError
        if usr_role is None:
            raise RoleNotFoundError
        if int(id) != current_user.id and not usr_role.can_create_users:
            raise AuthorizationError
        if edited_user is None:
            raise UserNotFoundError

        query = db.session().query
        usr_groups = query(UserGroup).filter_by(user=int(id)).all()

        for group in usr_groups:
            db.session.delete(group)

        for new_group in groups:
            if query(Group.id).filter_by(id=new_group).scalar() is None:
                raise GroupNotFoundError
            new_usrgroup = UserGroup(user=int(id), group=new_group)
            db.session.add(new_usrgroup)

        db.session.commit()

        response_body = {
            RESPONSE_MSG.SUCCESS: True,
            "user": expand_user_object(edited_user),
        }

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


@main_routes.route("/users/<id>", methods=["DELETE"])
@token_required
def delete_user(current_user, id):
    status_code = 200  # Success
    response_body = {}

    try:

        private_key = request.headers.get("private-key")
        usr_role = db.session.query(Role).get(current_user.role)
        edited_user = db.session.query(User).get(id)

        if private_key is None:
            raise MissingRequestKeyError
        if private_key != current_user.private_key:
            raise InvalidCredentialsError
        if usr_role is None:
            raise RoleNotFoundError
        if int(id) != current_user.id and not usr_role.can_create_users:
            raise AuthorizationError
        if edited_user is None:
            raise UserNotFoundError

        db.session.delete(edited_user)
        db.session.commit()

        response_body = {
            RESPONSE_MSG.SUCCESS: True,
            "user": expand_user_object(edited_user),
        }

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
def search_users(current_user):
    status_code = 200  # Success
    response_body = {}

    try:
        filters = loads(request.data)
        email = filters.get("email")
        role = filters.get("role")
        group = filters.get("group")

        private_key = request.headers.get("private-key")
        usr_role = db.session.query(Role).get(current_user.role)

        if email is None and role is None and group is None:
            raise MissingRequestKeyError
        if private_key is None:
            raise MissingRequestKeyError
        if private_key != current_user.private_key:
            raise InvalidCredentialsError
        if usr_role is None:
            raise RoleNotFoundError
        if not usr_role.can_triage_jobs:
            raise AuthorizationError

        query = db.session().query(User)
        for attr, value in filters.items():
            if attr != "group":
                query = query.filter(getattr(User, attr).like("%%%s%%" % value))
            else:
                query = query.join(UserGroup).filter(UserGroup.group.in_([group]))

        users = [expand_user_object(user) for user in query.all()]

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
