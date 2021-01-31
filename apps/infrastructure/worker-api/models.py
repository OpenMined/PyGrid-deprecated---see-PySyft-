from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Worker(db.Model):
    __tablename__ = "workers"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer())  # foreign key
    vCPU = db.Column(db.Integer())
    RAM = db.Column(db.Integer())
    storage = db.Column(db.Integer())
    GPU = db.Column(db.String(64))
    GPU_memory = db.Column(db.Integer())
    created_at = db.Column(db.DateTime, default=datetime.now())

    def __str__(self):
        return f"<Worker id: {self.id}, Instance: {self.instance_type}>"
