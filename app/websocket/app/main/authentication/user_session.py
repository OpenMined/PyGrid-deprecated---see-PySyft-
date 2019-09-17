from flask_login import UserMixin
from grid.auth import UserAuthentication
from flask import current_app
import uuid


class UserSession(UserMixin):
    def __init__(self, obj, active=True):
        self.id = uuid.uuid5(uuid.NAMESPACE_DNS, "openmined.org")
        self.obj = obj
        self.active = True

    def get_id(self):
        return self.id

    def username(self):
        return self.obj.username

    def is_active(self):
        return self.active

    def authenticate(self, payload):
        candidate_username = payload.get("user")
        candidate_password = payload.get("password")
        if candidate_username and candidate_password:
            return (
                self.obj.password == candidate_password
                and self.obj.username == candidate_username
            )
