from datetime import datetime

from .. import BaseModel, db

states = {"creating": 0, "failed": 1, "success": 2, "destroyed": 3}


class Environment(BaseModel):
    __tablename__ = "environment"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    state = db.Column(db.Integer)
    address = db.Column(db.String(255))
    syft_address = db.Column(db.String(255))
    provider = db.Column(db.String(64))
    region = db.Column(db.String(64))
    instance_type = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.now())
    destroyed_at = db.Column(db.DateTime, default=datetime.now())

    def __str__(self):
        return f"<Group id: {self.id}, name: {self.name}, state: {self.state}, address: {self.address}, syft_address: {self.syft_address}, provider: {self.provider}, region: {self.region}, instance_type: {self.instance_type}, created_at: {self.created_at}, destroyed_at: {self.destroyed_at}>"
