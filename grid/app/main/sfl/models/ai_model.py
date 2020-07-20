# External imports
import syft as sy

# Local imports
from ... import db


class Model(db.Model):
    """Model table that represents the AI Models.

    Columns:
        id (Int, Primary Key) : Model's id, used to recover stored model.
        version (String) : Model version.
        checkpoints (ModelCheckPoint) : Model Checkpoints. (One to Many relationship)
        fl_process_id (Integer, ForeignKey) : FLProcess Foreign Key.
    """

    __tablename__ = "static_model_"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    version = db.Column(db.String())
    checkpoints = db.relationship("ModelCheckPoint", backref="model")
    fl_process_id = db.Column(
        db.Integer, db.ForeignKey("static_fl_process_.id"), unique=True
    )

    def __str__(self):
        return f"<Model  id: {self.id}, version: {self.version}>"


class ModelCheckPoint(db.Model):
    """Model's save points.

    Columns:
        id (Integer, Primary Key): Checkpoint ID.
        values (Binary): Value of the model at a given checkpoint.
        model_id (String, Foreign Key): Model's ID.
    """

    __tablename__ = "static_model_checkpoint_"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    values = db.Column(db.LargeBinary)
    number = db.Column(db.Integer)
    alias = db.Column(db.String)
    model_id = db.Column(db.Integer, db.ForeignKey("static_model_.id"))

    @property
    def object(self):
        return sy.serde.deserialize(self.values)

    @object.setter
    def object(self):
        self.data = sy.serde.serialize(self.values)

    def __str__(self):
        return f"<CheckPoint id: {self.id}, number: {self.number}, alias: {self.alias}, model_id: {self.model_id}>"
