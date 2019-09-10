from ... import login_manager, socketio
import functools
from flask_login import current_user, login_user
from flask_socketio import emit, disconnect

from .user_session import UserSession

SESSION_TYPES = [UserSession]

from .session_repository import SessionsRepository

session_repository = SessionsRepository()

SESSION_TYPES = [UserSession]

# callback to reload the user object
@login_manager.user_loader
def load_user(userid):
    return session_repository.get_session_by_id(userid)


def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            emit("/auth", {"status": False})
            disconnect()
        else:
            return f(*args, **kwargs)

    return wrapped
