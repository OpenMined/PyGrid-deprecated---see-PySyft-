from .. import BaseModel, db


class Environment(BaseModel):
    __tablename__ = "environment"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    address = db.Column(db.String(255))
    url = db.Column(db.String(255))
    memory = db.Column(db.String(255))
    instance = db.Column(db.String(255))
    gpu = db.Column(db.String(255))

    def __str__(self):
        return f"<Group id: {self.id}, name: {self.name}, address: {self.address}, url: {self.url},memory: {self.memory}, instance: {self.instance}, gpu: {self.gpu}>"
