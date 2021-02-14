import json
from datetime import datetime

from flask import Flask, Response, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from apps.infrastructure.providers import AWS_Serverfull
from apps.infrastructure.providers.provider import Provider
from apps.infrastructure.utils import Config

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///workers.db"
db = SQLAlchemy(app)


class Worker(db.Model):
    __tablename__ = "workers"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    # user_id = db.Column(db.Integer())  # TODO: foreign key
    provider = db.Column(db.String(64))
    region = db.Column(db.String(64))
    instance = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.now())

    def __str__(self):
        return f"<Worker id: {self.id}, Instance: {self.instance_type}>"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@app.route("/deploy", methods=["POST"])
def create():
    """Creates a worker.
    This endpoint can be accessed by a user to create a new worker."""

    data = json.loads(request.json)
    config = Config(**data)

    deployed = True
    output = None

    if config.provider == "aws":
        aws_deployment = AWS_Serverfull(config=config)
        deployed, output = aws_deployment.deploy()
    elif config.provider == "azure":
        pass
    elif config.provider == "gcp":
        pass

    if deployed:
        worker = Worker(
            provider=config.provider,
            region=config.vpc.region,
            instance=config.vpc.instance_type.InstanceType,
        )
        db.session.add(worker)
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

    config = Config(app="worker", id=id)

    deleted = Provider(config).destroy()

    return Response(
        json.dumps({"deleted": deleted}), status=200, mimetype="application/json"
    )
