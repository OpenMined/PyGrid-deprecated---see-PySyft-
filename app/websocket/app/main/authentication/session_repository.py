from .user_session import UserSession
import grid
from grid.auth.config import read_authentication_configs
from grid.auth import AUTH_MODELS, UserAuthentication
from . import SESSION_TYPES


class SessionsRepository:
    def __init__(self):
        self.users = dict()
        self.users_id_dict = dict()
        self.__load_preset_credentials()

    def save_session(self, user, key):
        self.users[key] = user
        self.users_id_dict[user.id] = self.users[user.username]

    # Verify if already exists some user with these credentials
    def get_session(self):
        return self.users.get(username)

    # Recover user session by session id
    def get_session_by_id(self, sessionid):
        return self.users_id_dict.get(sessionid)

    def authenticate(self, payload):
        authenticated = False
        key = payload.get("user")
        session_object = self.users.get(key)
        if session_object:
            for session_type in SESSION_TYPES:
                if session_object.authenticate(payload):
                    authenticated = True
        if authenticated:
            return session_object

    def __load_preset_credentials(self):
        for cred in read_authentication_configs():
            for auth_type in AUTH_MODELS:
                if isinstance(cred, auth_type):
                    session = UserSession(cred)
                    self.save_session(session, session.username)
