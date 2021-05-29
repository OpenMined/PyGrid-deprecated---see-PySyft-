from sqlalchemy.sql import func

# grid relative
from .. import BaseModel
from .. import db


class UserGroup(BaseModel):
    __tablename__ = "usergroup"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    user = db.Column(db.Integer, db.ForeignKey("user.id"))
    group = db.Column(db.Integer, db.ForeignKey("group.id"))
    created_at = db.Column(db.DateTime(timezone=False), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=False), onupdate=func.now())
    deleted_at = db.Column(db.DateTime(timezone=False), default=None)

    def __str__(self):
        return f"<UserGroup id: {self.id}, user: {self.user}, " f"group: {self.group}>"
