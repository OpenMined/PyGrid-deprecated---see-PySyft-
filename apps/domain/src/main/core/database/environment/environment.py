# stdlib
from datetime import datetime

from sqlalchemy.sql import func

# grid relative
from .. import BaseModel
from .. import db

states = {"creating": 0, "failed": 1, "success": 2, "destroyed": 3}


class Environment(BaseModel):
    __tablename__ = "environment"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    state = db.Column(db.Integer)
    provider = db.Column(db.String(255))
    region = db.Column(db.String(255))
    instance_type = db.Column(db.String(255))
    address = db.Column(db.String(255), default="0.0.0.0")
    syft_address = db.Column(db.String(255), default="")  # TODO
    created_at = db.Column(db.DateTime(timezone=False), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=False), onupdate=func.now())
    deleted_at = db.Column(db.DateTime(timezone=False), default=None)

    def __str__(self):
        return f"<Group id: {self.id}, state: {self.state}, address: {self.address}, syft_address: {self.syft_address}, provider: {self.provider}, region: {self.region}, instance_type: {self.instance_type}, created_at: {self.created_at}, destroyed_at: {self.destroyed_at}>"
