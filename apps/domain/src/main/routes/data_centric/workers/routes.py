"""
from ..blueprint import dcfl_blueprint as dcfl_route
from flask import request, Response
import json

from syft.grid.messages.infra_messages import (
    CreateWorkerMessage,
    CheckWorkerDeploymentMessage,
    UpdateWorkerMessage,
    GetWorkerMessage,
    GetWorkersMessage,
    DeleteWorkerMessage,
)

from ...auth import error_handler, token_required
from ....core.task_handler import route_logic


## Nodes CRUD
@dcfl_route.route("/nodes", methods=["POST"])
@token_required
def create_node():
    def route_logic():
        # Get request body
        content = loads(request.data)

        syft_message = {}
        syft_message["message_class"] = ReprMessage  # TODO: CreateWorkerMessage
        syft_message["message_content"] = content
        syft_message[
            "sign_key"
        ] = node.signing_key  # TODO: Method to map token into sign-key

        # Execute task
        status_code, response_body = task_handler(
            route_function=process_as_syft_message,
            data=syft_message,
            mandatory={
                "message_class": MissingRequestKeyError,
                "message_content": MissingRequestKeyError,
                "sign_key": MissingRequestKeyError,
            },
        )
        return response_body

    # status_code, response_body = error_handler(process_as_syft_message)

    status_code, response_body = 200, {"msg": "Node created succesfully!"}

    return Response(
        json.dumps(response_body), status=status_code, mimetype="application/json"
    )


@dcfl_route.route("/nodes/<node_id>", methods=["GET"])
# @token_required
def get_node(node_id):
    def route_logic():
        # Get request body
        content = loads(request.data)

        syft_message = {}
        syft_message["message_class"] = ReprMessage  # TODO: GetWorkerMessage
        syft_message["message_content"] = content
        syft_message[
            "sign_key"
        ] = node.signing_key  # TODO: Method to map token into sign-key

        # Execute task
        status_code, response_body = task_handler(
            route_function=process_as_syft_message,
            data=syft_message,
            mandatory={
                "message_class": MissingRequestKeyError,
                "message_content": MissingRequestKeyError,
                "sign_key": MissingRequestKeyError,
            },
        )
        return response_body

    # status_code, response_body = error_handler(process_as_syft_message)

    status_code, response_body = 200, {
        "node": {"id": "464615", "tags": ["node-a"], "description": "node sample"}
    }

    return Response(
        json.dumps(response_body), status=status_code, mimetype="application/json"
    )


@dcfl_route.route("/nodes", methods=["GET"])
# @token_required
def get_all_nodes():
    def route_logic():
        # Get request body
        content = loads(request.data)

        syft_message = {}
        syft_message["message_class"] = ReprMessage  # TODO: GetAllWorkersMessage
        syft_message["message_content"] = content
        syft_message[
            "sign_key"
        ] = node.signing_key  # TODO: Method to map token into sign-key

        # Execute task
        status_code, response_body = task_handler(
            route_function=process_as_syft_message,
            data=syft_message,
            mandatory={
                "message_class": MissingRequestKeyError,
                "message_content": MissingRequestKeyError,
                "sign_key": MissingRequestKeyError,
            },
        )
        return response_body

    # status_code, response_body = error_handler(process_as_syft_message)
    status_code, response_body = 200, {
        "nodes": [
            {"id": "35654sad6ada", "address": "175.89.0.170"},
            {"id": "adfarf3f1af5", "address": "175.55.22.150"},
            {"id": "fas4e6e1fas", "address": "195.74.128.132"},
        ]
    }

    return Response(
        json.dumps(response_body), status=status_code, mimetype="application/json"
    )


@dcfl_route.route("/nodes/<node_id>", methods=["PUT"])
# @token_required
def update_node(node_id):
    def route_logic():
        # Get request body
        content = loads(request.data)

        syft_message = {}
        syft_message["message_class"] = ReprMessage  # TODO: UpdateWorkerMessage
        syft_message["message_content"] = content
        syft_message[
            "sign_key"
        ] = node.signing_key  # TODO: Method to map token into sign-key

        # Execute task
        status_code, response_body = task_handler(
            route_function=process_as_syft_message,
            data=syft_message,
            mandatory={
                "message_class": MissingRequestKeyError,
                "message_content": MissingRequestKeyError,
                "sign_key": MissingRequestKeyError,
            },
        )
        return response_body

    # status_code, response_body = error_handler(process_as_syft_message)
    status_code, response_body = 200, {"msg": "Node changed succesfully!"}

    return Response(
        json.dumps(response_body), status=status_code, mimetype="application/json"
    )


@dcfl_route.route("/nodes/<node_id>", methods=["DELETE"])
# @token_required
def delete_node(node_id):
    def route_logic():
        # Get request body
        content = loads(request.data)

        syft_message = {}
        syft_message["message_class"] = ReprMessage  # TODO: DeleteWorkerMessage
        syft_message["message_content"] = content
        syft_message[
            "sign_key"
        ] = node.signing_key  # TODO: Method to map token into sign-key

        # Execute task
        status_code, response_body = task_handler(
            route_function=process_as_syft_message,
            data=syft_message,
            mandatory={
                "message_class": MissingRequestKeyError,
                "message_content": MissingRequestKeyError,
                "sign_key": MissingRequestKeyError,
            },
        )
        return response_body

    # status_code, response_body = error_handler(process_as_syft_message)

    status_code, response_body = 200, {"msg": "Node deleted succesfully!"}

    return Response(
        json.dumps(response_body), status=status_code, mimetype="application/json"
    )


## Auto-scaling CRUD


@dcfl_route.route("/nodes/autoscaling", methods=["POST"])
# @token_required
def create_autoscaling():
    def route_logic():
        # Get request body
        content = loads(request.data)

        syft_message = {}
        syft_message["message_class"] = ReprMessage  # TODO: CreateAutoScalingMessage
        syft_message["message_content"] = content
        syft_message[
            "sign_key"
        ] = node.signing_key  # TODO: Method to map token into sign-key

        # Execute task
        status_code, response_body = task_handler(
            route_function=process_as_syft_message,
            data=syft_message,
            mandatory={
                "message_class": MissingRequestKeyError,
                "message_content": MissingRequestKeyError,
                "sign_key": MissingRequestKeyError,
            },
        )
        return response_body

    # status_code, response_body = error_handler(process_as_syft_message)
    status_code, response_body = 200, {
        "msg": "Autoscaling condition created succesfully!"
    }

    return Response(
        json.dumps(response_body), status=status_code, mimetype="application/json"
    )


@dcfl_route.route("/nodes/autoscaling", methods=["GET"])
# @token_required
def get_all_autoscaling_conditions():
    def route_logic():
        # Get request body
        content = loads(request.data)

        syft_message = {}
        syft_message[
            "message_class"
        ] = ReprMessage  # TODO: GetAutoScalingConditionsMessage
        syft_message["message_content"] = content
        syft_message[
            "sign_key"
        ] = node.signing_key  # TODO: Method to map token into sign-key

        # Execute task
        status_code, response_body = task_handler(
            route_function=process_as_syft_message,
            data=syft_message,
            mandatory={
                "message_class": MissingRequestKeyError,
                "message_content": MissingRequestKeyError,
                "sign_key": MissingRequestKeyError,
            },
        )
        return response_body

    # status_code, response_body = error_handler(process_as_syft_message)

    status_code, response_body = 200, {
        "condition_a": {"mem_usage": "80%", "cpu_usage": "90%", "disk_usage": "75%"},
        "condition_b": {"mem_usage": "50%", "cpu_usage": "70%", "disk_usage": "95%"},
        "condition_c": {"mem_usage": "92%", "cpu_usage": "77%", "disk_usage": "50%"},
    }

    return Response(
        json.dumps(response_body), status=status_code, mimetype="application/json"
    )


@dcfl_route.route("/nodes/autoscaling/<autoscaling_id>", methods=["GET"])
# @token_required
def get_specific_autoscaling_condition(autoscaling_id):
    def route_logic():
        # Get request body
        content = loads(request.data)

        syft_message = {}
        syft_message["message_class"] = ReprMessage  # TODO: GetAutoScalingCondition
        syft_message["message_content"] = content
        syft_message[
            "sign_key"
        ] = node.signing_key  # TODO: Method to map token into sign-key

        # Execute task
        status_code, response_body = task_handler(
            route_function=process_as_syft_message,
            data=syft_message,
            mandatory={
                "message_class": MissingRequestKeyError,
                "message_content": MissingRequestKeyError,
                "sign_key": MissingRequestKeyError,
            },
        )
        return response_body

    # status_code, response_body = error_handler(process_as_syft_message)

    status_code, response_body = 200, {
        "mem_usage": "80%",
        "cpu_usage": "90%",
        "disk_usage": "75%",
    }

    return Response(
        json.dumps(response_body), status=status_code, mimetype="application/json"
    )


@dcfl_route.route("/nodes/autoscaling/<autoscaling_id>", methods=["PUT"])
# @token_required
def update_autoscaling_condition(autoscaling_id):
    def route_logic():
        # Get request body
        content = loads(request.data)

        syft_message = {}
        syft_message["message_class"] = ReprMessage  # TODO: UpdateAutoScalingCondition
        syft_message["message_content"] = content
        syft_message[
            "sign_key"
        ] = node.signing_key  # TODO: Method to map token into sign-key

        # Execute task
        status_code, response_body = task_handler(
            route_function=process_as_syft_message,
            data=syft_message,
            mandatory={
                "message_class": MissingRequestKeyError,
                "message_content": MissingRequestKeyError,
                "sign_key": MissingRequestKeyError,
            },
        )
        return response_body

    # status_code, response_body = error_handler(process_as_syft_message)

    status_code, response_body = 200, {
        "msg": "Autoscaling condition updated succesfully!"
    }

    return Response(
        json.dumps(response_body), status=status_code, mimetype="application/json"
    )


@dcfl_route.route("/nodes/autoscaling/<autoscaling_id>", methods=["DELETE"])
# @token_required
def delete_autoscaling_condition(autoscaling_id):
    def route_logic():
        # Get request body
        content = loads(request.data)

        syft_message = {}
        syft_message["message_class"] = ReprMessage  # TODO: DeleteAutoScalingCondition
        syft_message["message_content"] = content
        syft_message[
            "sign_key"
        ] = node.signing_key  # TODO: Method to map token into sign-key

        # Execute task
        status_code, response_body = task_handler(
            route_function=process_as_syft_message,
            data=syft_message,
            mandatory={
                "message_class": MissingRequestKeyError,
                "message_content": MissingRequestKeyError,
                "sign_key": MissingRequestKeyError,
            },
        )
        return response_body

    # status_code, response_body = error_handler(process_as_syft_message)

    status_code, response_body = 200, {
        "msg": "Autoscaling condition deleted succesfully!"
    }

    return Response(
        json.dumps(response_body), status=status_code, mimetype="application/json"
    )


## Workers CRUD
@dcfl_route.route("/workers", methods=["POST"])
@token_required
def create_node(current_user):
    # Get request body
    content = json.loads(request.data)

    if not content:
        content = {}

    status_code, response_msg = error_handler(
        route_logic, CreateWorkerMessage, current_user, content
    )

    response = response_msg if isinstance(response_msg, dict) else response_msg.content

    return Response(
        json.dumps(response),
        status=status_code,
        mimetype="application/json",
    )


@dcfl_route.route("/workers/<worker_id>", methods=["GET"])
@token_required
def get_worker(current_user, worker_id):
    # Get request body
    content = request.get_json()
    if not content:
        content = {}

    content["worker_id"] = worker_id

    status_code, response_msg = error_handler(
        route_logic, GetWorkerMessage, current_user, content
    )
    response = response_msg if isinstance(response_msg, dict) else response_msg.content

    return Response(
        json.dumps(response),
        status=status_code,
        mimetype="application/json",
    )


@dcfl_route.route("/workers", methods=["GET"])
@token_required
def get_all_nodes(current_user):
    # Get request body
    content = request.get_json()
    if not content:
        content = {}
    status_code, response_msg = error_handler(
        route_logic, GetWorkersMessage, current_user, content
    )

    response = response_msg if isinstance(response_msg, dict) else response_msg.content
    return Response(
        json.dumps(response),
        status=status_code,
        mimetype="application/json",
    )


@dcfl_route.route("/workers/<worker_id>", methods=["PUT"])
@token_required
def update_node(current_user, worker_id):
    # Get request body
    content = request.get_json()
    if not content:
        content = {}
    content["worker_id"] = worker_id

    status_code, response_msg = error_handler(
        route_logic, UpdateWorkerMessage, current_user, content
    )
    response = response_msg if isinstance(response_msg, dict) else response_msg.content
    return Response(
        json.dumps(response),
        status=status_code,
        mimetype="application/json",
    )


@dcfl_route.route("/workers/<worker_id>", methods=["DELETE"])
@token_required
def delete_node(current_user, worker_id):
    # Get request body
    content = request.get_json()
    if not content:
        content = {}
    content["worker_id"] = worker_id

    status_code, response_msg = error_handler(
        route_logic, DeleteWorkerMessage, current_user, content
    )

    response = response_msg if isinstance(response_msg, dict) else response_msg.content
    return Response(
        json.dumps(response),
        status=status_code,
        mimetype="application/json",
    )
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from .......infrastructure import AWS_Serverfull, Config, Provider
from ....core.database import db
from ....core.database.workers.worker import Worker, states
from ..blueprint import dcfl_blueprint as dcfl_route


def get_config(data):
    """Reads environment variables from the domain instance to create a Config
    object for deploying the worker."""
    return Config(
        app=Config(name="worker", count=1, id=db.session.query(Worker).count() + 1),
        apps=[Config(name="worker", count=1)],
        serverless=False,
        websockets=False,
        provider=os.environ["CLOUD_PROVIDER"],
        vpc=Config(
            region=os.environ["REGION"], instance_type=Config(**data["instance_type"])
        ),
    )


@dcfl_route.route("/check")
def check():
    response = {"message": "Can access worker api"}
    return Response(json.dumps(response), status=200, content_type="application/json")


@dcfl_route.route("/workers/deploy", methods=["POST"])
def create():
    """Creates a worker.
    This endpoint can be accessed by a user to create a new worker."""

    # data = json.loads(request.json)
    config = get_config(request.json)
    print(config)

    deployment = None
    deployed = False
    output = {}

    if config.provider == "aws":
        deployment = AWS_Serverfull(config=config)
    elif config.provider == "azure":
        pass
    elif config.provider == "gcp":
        pass

    if deployment.validate():
        worker = Worker(
            id=config.app.id,
            provider=config.provider,
            region=config.vpc.region,
            instance=config.vpc.instance_type.InstanceType,
            state=states["creating"],
        )
        db.session.add(worker)
        db.session.commit()

        deployed, output = deployment.deploy()  # Deploy
        # time.sleep(5)
        # deployed = False
        # output = {}

        worker = Worker.query.get(config.app.id)
        if deployed:
            worker.state = states["success"]
            worker.deployed_at = datetime.now()
        else:
            worker.state = states["failed"]
        db.session.commit()

    response = {"deloyed": deployed, "output": output}
    return Response(json.dumps(response), status=200, mimetype="application/json")


@dcfl_route.route("/workers", methods=["GET"])
def get_workers():
    """Get all deployed workers.
    Only Node operators can access this endpoint.
    """
    workers = Worker.query.order_by(Worker.created_at).all()
    return Response(
        json.dumps([worker.as_dict() for worker in workers], default=str),
        status=200,
        mimetype="applications/json",
    )


@dcfl_route.route("/workers/<int:id>", methods=["GET"])
def get_worker(id):
    """Get specific worker data.
    Only the Node owner and the user who created this worker can access this endpoint.
    """
    worker = Worker.query.get(id)
    return Response(
        json.dumps(worker.as_dict(), default=str),
        status=200,
        mimetype="applications/json",
    )


@dcfl_route.route("/workers/<int:id>", methods=["DELETE"])
def delete_worker(id):
    """Shut down specific worker.
    Only the Node owner and the user who created this worker can access this endpoint.
    """
    worker = Worker.query.get(id)
    if worker.state == states["success"]:
        config = Config(provider=worker.provider, app=Config(name="worker", id=id))
        success = Provider(config).destroy()
        if success:
            worker.state = states["destroyed"]
            worker.destroyed_at = datetime.now()
            db.session.commit()
        return Response(
            json.dumps({"deleted": success}), status=200, mimetype="application/json"
        )
    else:
        return Response(status=404, mimetype="application/json")
