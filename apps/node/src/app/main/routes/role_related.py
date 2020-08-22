from json import dumps, loads
from json.decoder import JSONDecodeError
import logging

from flask import Response, request
from syft.codes import RESPONSE_MSG

from ..core.exceptions import (
    UserNotFoundError,
    RoleNotFoundError,
    AuthorizationError,
    PyGridError,
    MissingRequestKeyError,
)
from .. import main_routes
from ..database import Role, User
from ... import BaseModel, db


def to_json(model):
    """Returns a JSON representation of an SQLAlchemy-backed object."""
    json = {}

    for col in model._sa_class_manager.mapper.mapped_table.columns:
        json[col.name] = getattr(model, col.name)

    return json


def identify_user(request):
    private_key = request.headers.get("private-key")
    if private_key is None:
        raise MissingRequestKeyError

    usr = db.session.query(User).filter_by(private_key=private_key).one_or_none()
    if usr is None:
        raise UserNotFoundError

    usr_role = db.session.query(Role).get(usr.role)
    if usr_role is None:
        raise RoleNotFoundError

    return usr, usr_role


@main_routes.route("/roles", methods=["POST"])
def create_role():
    status_code = 200  # Success
    response_body = {}
    body = loads(request.data)

    try:

        usr, usr_role = identify_user(request)
        if not usr_role.can_edit_roles:
            raise AuthorizationError

        new_role = Role(**body)
        db.session.add(new_role)
        db.session.commit()
        response_body = {RESPONSE_MSG.SUCCESS: True, "role": to_json(new_role)}

    except AuthorizationError as e:
        status_code = 403  # Unathorized
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User not authorized to post-role", exc_info=e)
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


@main_routes.route("/roles/<id>", methods=["GET"])
def get_role(id):
    status_code = 200  # Success
    response_body = {}

    try:

        usr, usr_role = identify_user(request)
        if not usr_role.can_triage_jobs:
            raise AuthorizationError

        role = db.session.query(Role).get(id)
        if role is None:
            raise RoleNotFoundError

        response_body = to_json(role)
        response_body = {RESPONSE_MSG.SUCCESS: True, "role": to_json(role)}

    except AuthorizationError as e:
        status_code = 403  # Unathorized
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User not authorized to post-role", exc_info=e)
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


@main_routes.route("/roles", methods=["GET"])
def get_all_roles():
    status_code = 200  # Success
    response_body = {}

    try:

        usr, usr_role = identify_user(request)
        if not usr_role.can_triage_jobs:
            raise AuthorizationError

        roles = db.session.query(Role).all()
        roles = [to_json(r) for r in roles]
        response_body = {RESPONSE_MSG.SUCCESS: True, "roles": roles}

    except AuthorizationError as e:
        status_code = 403  # Unathorized
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User not authorized to post-role", exc_info=e)
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


@main_routes.route("/roles/<id>", methods=["PUT"])
def put_role(id):
    status_code = 200  # Success
    response_body = {}
    body = loads(request.data)

    try:

        usr, usr_role = identify_user(request)
        if not usr_role.can_edit_roles:
            raise AuthorizationError

        role = db.session.query(Role).get(id)
        if role is None:
            raise RoleNotFoundError

        for key, value in body.items():
            setattr(role, key, value)

        db.session.commit()
        response_body = {RESPONSE_MSG.SUCCESS: True, "role": to_json(role)}

    except AuthorizationError as e:
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


@main_routes.route("/roles/<id>", methods=["DELETE"])
def delete_role(id):
    status_code = 200  # Success
    response_body = {}

    try:

        usr, usr_role = identify_user(request)
        if not usr_role.can_edit_roles:
            raise AuthorizationError

        role = db.session.query(Role).get(id)
        if role is None:
            raise RoleNotFoundError
        db.session.delete(role)
        db.session.commit()
        response_body = {RESPONSE_MSG.SUCCESS: True}

    except AuthorizationError as e:
        status_code = 403  # Unathorized
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User not authorized to post-role", exc_info=e)
    except (RoleNotFoundError, UserNotFoundError) as e:
        status_code = 404  # Resource not found
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("User/Role not found in delete-role", exc_info=e)
    except (TypeError, MissingRequestKeyError, PyGridError, JSONDecodeError) as e:
        status_code = 400  # Bad Request
        response_body[RESPONSE_MSG.ERROR] = str(e)
    except Exception as e:
        status_code = 500  # Internal Server Error
        response_body[RESPONSE_MSG.ERROR] = str(e)

    return Response(
        dumps(response_body), status=status_code, mimetype="application/json"
    )
