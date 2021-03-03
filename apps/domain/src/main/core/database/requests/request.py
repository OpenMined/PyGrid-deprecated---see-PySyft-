from .. import BaseModel, db


class Request(BaseModel):
    """Request.

    Columns:
        id (Integer, Primary Key): Cycle ID.
        date (TIME): Start time.
        user_id (Integer, Foregn Key): 
        object_id (Integer):
        status (String): The status of the request, wich can be 'pending', 'accepted' or 'denied'.
    """

    __tablename__ = "request"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    object_id = db.Column(db.Integer())
    status = db.Column(db.String(255), default='pending')

    def __str__(self):
        return f"< Request id : {self.id}, user: {self.user_id},  Date: {self.date}, Object: {self.object_id}, status: {self.status} >"
