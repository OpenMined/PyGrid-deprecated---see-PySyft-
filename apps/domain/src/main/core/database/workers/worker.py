from datetime import datetime

from .. import db

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
