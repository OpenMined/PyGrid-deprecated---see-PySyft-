from .. import local_worker
from flask_login import LoginManager, current_user
import functools
from .user_session import UserSession
import json


SESSION_TYPES = [UserSession]
from .session_repository import SessionsRepository


session_repository = None
login_manager = LoginManager()


def set_auth_configs(app):
    """ Set configs to use flask session manager

        Args:
            app: Flask application
        Returns:
            app: Flask application
    """
    global session_repository
    login_manager.init_app(app)
    session_repository = SessionsRepository()
    return app


def get_session():
    global session_repository
    return session_repository


# callback to reload the user object
@login_manager.user_loader
def load_user(userid):
    return session_repository.get_session_by_id(userid)


def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            current_user.worker = local_worker
            return f(*args, **kwargs)
        else:
            return f(*args, **kwargs)

    return wrapped
