from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class GridNodes(db.Model):
    """ Grid Nodes table that represents connected grid nodes.
    
        Collumns:
            id (primary_key) : node id, used to recover stored grid nodes (UNIQUE).
            address: Address of grid node.
    """

    __tablename__ = "__gridnode__"

    id = db.Column(db.String(64), primary_key=True)
    address = db.Column(db.String(64))

    def __str__(self):
        return f"< Grid Node {self.id} : {self.address}>"


class FLProcess(db.Model):
    """ Federated Learning Process """

    __tablename__ = "__fl_process__"

    id = db.Column(db.String(64), primary_key=True)

    def __str__(self):
        return f"FL Process {self.id}"
