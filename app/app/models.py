from app import db
import syft as sy

class Tensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(64), index=True, unique=True)
    tensorb = db.Column(db.Binary(64))

    def tensor(self):
        return sy.serde.deserialize(self.tensorb)

    def __repr__(self):
        return f'<Tensor {self.id}>'
