import os
import json
from pathlib import Path
from flask import Flask, Response, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from .providers.aws import AWS_Serverfull, AWS_Serverless

# from .models import *

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///myDatabase.db"
# db.init_app(app)

# hack
app.app_context().push()
# db.create_all()
# app.app_context().pop()


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

    deployed = False
    output = None

    if provider == "aws":
        if serverless:
            aws_deployment = AWS_Serverless(
                credentials=data["credentials"]["cloud"],
                vpc_config=data["vpc"],
                db_config=data["credentials"]["db"],
                app_config=data["app"],
            )
            deployed, output = aws_deployment.deploy()
        else:
            pass
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
