from grid.auth.config import read_authentication_configs
from grid.auth import AUTH_MODELS, UserAuthentication
from .user_session import UserSession


class SessionsRepository(object):
    DEFAULT_MANAGER_USER = "admin"
    DEFAULT_MANAGER_PASSWORD = "admin"

    def __init__(self):
        self.users = dict()
        self.users_id_dict = dict()
        self._admin = UserSession(self.__load_node_manager())
        self.save_session(self._admin, self._admin.username())

    def save_session(self, user, key):
        self.users[key] = user
        self.users_id_dict[user.id] = self.users[user.username()]

    # Verify if already exists some user with these credentials
    def get_session(self, username):
        return self.users.get(username)

    # Recover user session by session id
    def get_session_by_id(self, sessionid):
        return self.users_id_dict.get(sessionid)

    def authenticate(self, payload):
        key = payload.get("user")
        session_object = self.users.get(key)
        if session_object:
            if session_object.authenticate(payload):
                return session_object

    def __load_node_manager(self):
        return UserAuthentication(
            SessionsRepository.DEFAULT_MANAGER_USER,
            SessionsRepository.DEFAULT_MANAGER_PASSWORD,
        )

    def __load_preset_credentials(self):
        for cred in read_authentication_configs():
            for auth_type in AUTH_MODELS:
                if isinstance(cred, auth_type):
                    session = UserSession(cred)
                    self.save_session(session, session.username())
