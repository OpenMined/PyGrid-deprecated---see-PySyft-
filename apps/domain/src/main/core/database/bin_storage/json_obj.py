from sqlalchemy.sql import func

# grid relative
from .. import BaseModel
from .. import db


class JsonObject(BaseModel):
    __bind_key__ = "bin_store"
    __tablename__ = "json_object"

    id = db.Column(db.String(), primary_key=True)
    binary = db.Column(db.JSON())
    created_at = db.Column(db.DateTime(timezone=False), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=False), onupdate=func.now())
    deleted_at = db.Column(db.DateTime(timezone=False), default=None)

    def __str__(self):
        return f"<JsonObject id: {self.id}>"
