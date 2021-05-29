from sqlalchemy.sql import func

# grid relative
from .. import BaseModel
from .. import db


class Group(BaseModel):
    __tablename__ = "group"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=False), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=False), onupdate=func.now())
    deleted_at = db.Column(db.DateTime(timezone=False), default=None)

    def __str__(self):
        return f"<Group id: {self.id}, name: {self.name}>"
