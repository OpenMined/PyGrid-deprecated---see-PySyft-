import os
import json
from pathlib import Path
from flask import Flask, Response, jsonify, request
from ..utils import Config
from loguru import logger

from .providers.aws import AWS_Serverfull, AWS_Serverless

app = Flask(__name__)


@app.route("/")
def index():
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

    provider = data.get("provider").lower()
    serverless = data.get("serverless")
    websockets = data.get("websockets")

    config_data = Config(**data)
    logger.debug(config_data)

    deployed = False
    output = None

    if provider == "aws":
        if serverless:
            ## Todo: Make serverless class work with config object
            aws_deployment = AWS_Serverless(
                credentials=data["credentials"]["cloud"],
                vpc_config=data["vpc"],
                db_config=data["credentials"]["db"],
                app_config=data["app"],
            )
            deployed, output = aws_deployment.deploy()
        else:
            pass
            # aws_deployment = AWS_Serverfull(
            #     # config=config_data,
            #     credentials=data["credentials"]["cloud"],
            #     vpc_config=data["vpc"],
            # )
            # aws_deployment.deploy()
    elif provider == "azure":
        pass
    elif provider == "gcp":
        pass

    if deployed:
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
