import os
import json
from pathlib import Path
from flask import Flask, Response, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from .providers.aws import AWS_Serverfull, AWS_Serverless

from .models import *

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///myDatabase.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


@app.route("/")
def index():
    db.create_all()
    response = {
        "message": "Welcome to OpenMined PyGrid Infrastructure Deployment Suite"
    }
    return Response(json.dumps(response), status=200, mimetype="application/json")


@app.route("/deploy", methods=["POST"])
def deploy():
    """
    Deploys the resources.
    """

    data = json.loads(request.json)

    app_config = data["app"]
    db_config = data["credentials"]["db"]
    provider = data.get("provider").lower()
    serverless = data.get("serverless")
    websockets = data.get("websockets")

    deployed = False
    output = None

    if provider == "aws":
        if serverless:
            aws_deployment = AWS_Serverless(
                credentials=data["credentials"]["cloud"],
                vpc_config=data["vpc"],
                db_config=db_config,
                app_config=app_config,
            )
            deployed, output = aws_deployment.deploy()
        else:
            pass
    elif provider == "azure":
        pass
    elif provider == "gcp":
        pass

    if deployed:
        kwargs = {
            "provider": provider,
            "serverless": serverless,
            "websockets": websockets,
            "db_username": db_config["username"],
            "db_password": db_config["password"],
            "region": data["vpc"]["region"],
            "av_zones": ",".join(
                list(data["vpc"]["av_zones"])
            ),  # List of strings stored as comma separated values
        }
        if app_config["name"] == "node":
            db.session.add(
                Node(
                    node_id=app_config["id"],
                    network=app_config["network"],
                    port=app_config.get("port"),
                    host=app_config.get("host"),
                    **kwargs,
                )
            )
        elif app_config["name"] == "network":
            db.session.add(
                Network(
                    host=app_config.get("host"), port=app_config.get("port"), **kwargs
                )
            )
        db.session.commit()
        status_code = 200
        response = {
            "message": f"Your PyGrid {data['app']['name']} was deployed successfully",
            "output": output,
        }
    else:
        status_code = 400
        response = {
            "message": f"Your attempt to deploy PyGrid {data['app']['name']} failed",
            "error": output,
        }

    return Response(
        json.dumps(response), status=status_code, mimetype="application/json"
    )


def app_to_dict(app):
    return {
        "id": app.id,
        "provider": app.provider,
        "serverless": app.serverless,
        "websockets": app.websockets,
        "db_username": app.db_username,
        "db_password": app.db_password,
        "region": app.region,
        "av_zones": list(app.av_zones.split(",")),
    }


def node_to_dict(node):
    app = app_to_dict(node)
    app["node_id"] = node.node_id
    app["network"] = node.network
    app["port"] = node.port
    app["host"] = node.host
    return app


def network_to_dict(network):
    app = app_to_dict(network)
    app["port"] = network.port
    app["host"] = network.host
    return app


@app.route("/deployed/nodes")
def get_deployed_nodes():
    """
    Returns info about all the deployed nodes.
    """

    return Response(
        json.dumps(
            [node_to_dict(node) for node in Node.query.order_by("deployed_at").all()]
        ),
        status=200,
        mimetype="application/json",
    )


@app.route("/deployed/node/<id>")
def get_deployed_node(id):
    """
    Returns info about a given deployed node.
    """
    return Response(
        json.dumps(node_to_dict(Node.query.get(id))),
        status=200,
        mimetype="application/json",
    )


@app.route("/deployed/networks")
def get_deployed_networks():
    """
    Returns info about all the deployed networks.
    """
    return Response(
        json.dumps(
            [
                network_to_dict(network)
                for network in Network.query.order_by("deployed_at").all()
            ]
        ),
        status=200,
        mimetype="application/json",
    )


@app.route("/deployed/network/<id>")
def get_deployed_network(id):
    """
    Returns info about a given deployed network.
    """
    return Response(
        json.dumps(network_to_dict(Network.query.get(id))),
        status=200,
        mimetype="application/json",
    )
