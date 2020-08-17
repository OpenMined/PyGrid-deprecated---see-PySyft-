from json import dumps, loads

from flask import Response, request
from syft.codes import RESPONSE_MSG

from ..core.exceptions import InvalidRequestKeyError, PyGridError
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
        # TODO except missing row in db
        role = db.session.query(Role).get(id)
        response_body = to_json(role)
        response_body = {RESPONSE_MSG.SUCCESS: True, "role": to_json(role)}
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
    roles = db.session.query(Role).all()
    roles = [to_json(r) for r in roles]
    response_body = {RESPONSE_MSG.SUCCESS: True, "roles": roles}

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
        for key, value in body.items():
            setattr(role, key, value)

        db.session.commit()
        response_body = {RESPONSE_MSG.SUCCESS: True, "role": to_json(role)}
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
        db.session.delete(role)
        db.session.commit()
        response_body = {RESPONSE_MSG.SUCCESS: True}
    except (TypeError, PyGridError, json.decoder.JSONDecodeError) as e:
        status_code = 400  # Bad Request
        response_body[RESPONSE_MSG.ERROR] = str(e)
    except Exception as e:
        status_code = 500  # Internal Server Error
        response_body[RESPONSE_MSG.ERROR] = str(e)

    return Response(
        dumps(response_body), status=status_code, mimetype="application/json"
    )
