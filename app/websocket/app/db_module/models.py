from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
import syft as sy


class Worker(db.Model):
    __tablename__ = "workers"

    id = db.Column(db.String(64), primary_key=True)
    worker_objects = db.relationship("WorkerObject", lazy="dynamic")

    def __repr__(self):
        return f"<Worker {self.id}>"


class WorkerObject(db.Model):
    __tablename__ = "worker_objects"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(64), index=True, unique=True)
    data = db.Column(db.LargeBinary(128))
    worker_id = db.Column(db.String(64), db.ForeignKey("workers.id"))

    def __init__(self, **kwargs):
        super(WorkerObject, self).__init__(**kwargs)

    @property
    def object(self):
        return sy.serde.deserialize(self.data)

    @object.setter
    def object(self, value):
        self.data = sy.serde.serialize(value, force_full_simplification=True)

    def __repr__(self):
        return f"<Tensor {self.id}>"
