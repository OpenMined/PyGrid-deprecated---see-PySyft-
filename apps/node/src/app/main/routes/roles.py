from json import dumps, loads
import logging

from flask import Response, request
from syft.codes import RESPONSE_MSG

from ..core.exceptions import RoleNotFoundError
from .. import main_routes
from ..database import Role
from ... import BaseModel, db

from json import dumps


def to_json(model):
    """Returns a JSON representation of an SQLAlchemy-backed object."""
    json = {}

    for col in model._sa_class_manager.mapper.mapped_table.columns:
        json[col.name] = getattr(model, col.name)

    return json


@main_routes.route("/roles", methods=["POST"])
def create_role():
    status_code = 200  # Success
    response_body = {}
    body = loads(request.data)

    try:
        new_role = Role(**body)
        db.session.add(new_role)
        db.session.commit()
        response_body = {RESPONSE_MSG.SUCCESS: True, "role": to_json(new_role)}
    except (TypeError, PyGridError, json.decoder.JSONDecodeError) as e:
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
        role = db.session.query(Role).get(id)
        if role is None:
            raise RoleNotFoundError

        response_body = to_json(role)
        response_body = {RESPONSE_MSG.SUCCESS: True, "role": to_json(role)}
    except RoleNotFoundError as e:
        status_code = 404
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("Role not found in get-role", exc_info=e)
    except (TypeError, PyGridError, json.decoder.JSONDecodeError) as e:
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
        roles = db.session.query(Role).all()
        roles = [to_json(r) for r in roles]
        response_body = {RESPONSE_MSG.SUCCESS: True, "roles": roles}
    except (TypeError, PyGridError, json.decoder.JSONDecodeError) as e:
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
        role = db.session.query(Role).get(id)
        if role is None:
            raise RoleNotFoundError

        for key, value in body.items():
            setattr(role, key, value)

        db.session.commit()
        response_body = {RESPONSE_MSG.SUCCESS: True, "role": to_json(role)}
    except RoleNotFoundError as e:
        status_code = 404
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("Role not found in put-role", exc_info=e)
    except (TypeError, PyGridError, json.decoder.JSONDecodeError) as e:
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
        role = db.session.query(Role).get(id)
        if role is None:
            raise RoleNotFoundError
        db.session.delete(role)
        db.session.commit()
        response_body = {RESPONSE_MSG.SUCCESS: True}
    except RoleNotFoundError as e:
        status_code = 404
        response_body[RESPONSE_MSG.ERROR] = str(e)
        logging.warning("Role not found in delete-role", exc_info=e)
    except (TypeError, PyGridError, json.decoder.JSONDecodeError) as e:
        status_code = 400  # Bad Request
        response_body[RESPONSE_MSG.ERROR] = str(e)
    except Exception as e:
        status_code = 500  # Internal Server Error
        response_body[RESPONSE_MSG.ERROR] = str(e)

    return Response(
        dumps(response_body), status=status_code, mimetype="application/json"
    )
