import json

from flask import Flask, Response, jsonify, request

from apps.infrastructure.providers import AWS_Serverfull, AWS_Serverless
from apps.infrastructure.providers.provider import Provider
from apps.infrastructure.utils import Config

from .models import Worker, db

app = Flask(__name__)
db.init_app(app)


@app.route("/workers", methods=["POST"])
def create():
    """Deploys a worker."""

    data = json.loads(request.json)
    config = Config(**data)

    deployed = False
    output = None

    if config.provider == "aws":
        aws_deployment = AWS_Serverfull(config=config)
        deployed, output = aws_deployment.deploy()
    elif config.provider == "azure":
        pass
    elif config.provider == "gcp":
        pass

    response = {"deloyed": deployed, "output": output}
    return Response(json.dumps(response), status=200, mimetype="application/json")


@app.route("/workers", methods=["GET"])
def get_workers():
    """Get all deployed workers.
    Only Node operators can access this endpoint.
    """
    # TODO: SHOULD WE ALLOW THE USER TO ACCESS ALL IT'S DEPLOYMENTS THROUGH THIS ENDPOINT ?
    workers = Worker.query.order_by(Worker.created_at).all()
    return Response(json.dumps(workers), status=200, mimetype="applications/json")


@app.route("/workers/<int:id>", methods=["GET"])
def get_worker(id):
    """Get specific worker data.
    Only the Node owner and the user who created this worker can access this endpoint.
    """
    try:
        worker = Worker.query.get(id)
        return Response(json.dumps(worker), status=200, mimetype="applications/json")
    except:
        response = {"message": "Worker Not Found"}
        return Response(json.dumps(response), status=404, mimetype="applications/json")


@app.route("/workers/<int:id>", methods=["DELETE"])
def delete_worker(id):
    """Shut down specific worker.
    Only the Node owner and the user who created this worker can access this endpoint.
    """

    config = Config(app="worker", id=id)

    deleted = Provider(config).destroy()

    return Response(
        json.dumps({"deleted": deleted}), status=200, mimetype="application/json"
    )
