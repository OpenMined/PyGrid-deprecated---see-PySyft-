import json
import os
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from apps.infrastructure.providers import AWS_Serverfull
from apps.infrastructure.providers.provider import Provider
from apps.infrastructure.utils import Config

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///workers.db"
db = SQLAlchemy(app)

states = {"creating": 0, "failed": 1, "success": 2, "destroyed": 3}


class Worker(db.Model):
    __tablename__ = "workers"

    id = db.Column(db.Integer(), primary_key=True)
    # user_id = db.Column(db.Integer())  # TODO: foreign key
    provider = db.Column(db.String(64))
    region = db.Column(db.String(64))
    instance = db.Column(db.String(64))
    state = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.now())
    destroyed_at = db.Column(db.DateTime, default=datetime.now())

    def __str__(self):
        return f"<Worker id: {self.id}, Instance: {self.instance_type}>"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


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


@app.route("/deploy", methods=["POST"])
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


@app.route("/workers", methods=["GET"])
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


@app.route("/workers/<int:id>", methods=["GET"])
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


@app.route("/workers/<int:id>", methods=["DELETE"])
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
