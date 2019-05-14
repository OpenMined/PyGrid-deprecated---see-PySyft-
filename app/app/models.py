from app import db
import syft as sy

class WorkerObject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(64), index=True, unique=True)
    data = db.Column(db.Binary(64))

    def object(self):
        return sy.serde.deserialize(self.data)

    def __repr__(self):
        return f'<Tensor {self.id}>'

class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(64), index=True, unique=True)

    def tensor(self):
        return sy.serde.deserialize(self.tensorb)

    def __repr__(self):
        return f'<Tensor {self.id}>'
