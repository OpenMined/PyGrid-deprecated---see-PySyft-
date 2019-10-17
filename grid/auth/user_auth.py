import uuid
import glob
import os.path
import json
from .authentication import BaseAuthentication


class UserAuthentication(BaseAuthentication):
    FILENAME = "auth.user"

    def __init__(self, username, password):
        """ Initialize a user authentication object.
            Args:
                username (str) : Key to identify this object.
                password (str) : Secret used to verify and validate this object.
        """
        self.username = username
        self.password = password
        super().__init__(UserAuthentication.FILENAME)

    @staticmethod
    def parse(path):
        """ Static method used to create new user authentication instances parsing a json file.
            
            Args:
                path (str) : json file path.
            Returns:
                List : List of user authentication objects.
        """
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
        """ Reprensents user authentication object in a JSON/dict data structure. """
        return {"user": self.username, "password": self.password}
