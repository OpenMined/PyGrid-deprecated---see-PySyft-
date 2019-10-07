import uuid
import glob
import os.path
import json
from .authentication import BaseAuthentication


class UserAuthentication(BaseAuthentication):

    FILENAME = "auth.user"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        super().__init__(UserAuthentication.FILENAME)

    @staticmethod
    def parse(path):
        user_files = glob.glob(os.path.join(path, UserAuthentication.FILENAME))
        users = []
        for f in user_files:
            with open(f) as json_file:
                credentials = json.load(json_file)
                cred_users = credentials["credential"]
                for user in cred_users:
                    new_user = UserAuthentication(user["username"], user["password"])
                    users.append(new_user)
        return users

    def json(self):
        return {"user": self.username, "password": self.password}
