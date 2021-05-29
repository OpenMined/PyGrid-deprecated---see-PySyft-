from sqlalchemy.sql import func

# grid relative
from .. import BaseModel
from .. import db


class Association(BaseModel):
    """Association.

    Columns:
        id (Integer, Primary Key): Cycle ID.
        date (TIME): Start time.
        network (String): Network name.
        network_address (String) : Network Address.
    """

    __tablename__ = "association"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime())
    name = db.Column(db.String(255))
    address = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=False), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=False), onupdate=func.now())
    deleted_at = db.Column(db.DateTime(timezone=False), default=None)

    def __str__(self):
        return f"< Association id : {self.id}, Name: {self.name}, Address: {self.address}, Date: {self.date}>"
