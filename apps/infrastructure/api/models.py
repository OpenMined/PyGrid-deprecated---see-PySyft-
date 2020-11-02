from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Node(db.Model):
    __tablename__ = "nodes"
    id = db.Column(db.Integer, primary_key=True)

    provider = db.Column(db.String(32), nullable=False)
    deployed_at = db.Column(db.DateTime, default=datetime.now())
    serverless = db.Column(db.Boolean, nullable=False)
    websockets = db.Column(db.Boolean, nullable=False)
    db_username = db.Column(db.String(64), nullable=False)
    db_password = db.Column(db.String(64), nullable=False)  # TODO: Hash/encrypt?
    region = db.Column(db.String(64), nullable=False)
    av_zones = db.Column(db.String(128))

    node_id = db.Column(db.String(64), nullable=False)
    network = db.Column(db.String(64), nullable=False)
    host = db.Column(db.String(64))  # , nullable=False)
    port = db.Column(db.Integer)


class Network(db.Model):
    __tablename__ = "networks"
    id = db.Column(db.Integer, primary_key=True)

    provider = db.Column(db.String(32), nullable=False)
    deployed_at = db.Column(db.DateTime, default=datetime.now())
    serverless = db.Column(db.Boolean, nullable=False)
    websockets = db.Column(db.Boolean, nullable=False)
    db_username = db.Column(db.String(64), nullable=False)
    db_password = db.Column(db.String(64), nullable=False)  # TODO: Hash/Encrypt?
    region = db.Column(db.String(64), nullable=False)
    av_zones = db.Column(db.String(128))

    host = db.Column(db.String(64))  # , nullable=False)
    port = db.Column(db.Integer)
