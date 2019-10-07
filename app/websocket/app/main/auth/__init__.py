from ... import login_manager
from flask_login import current_user
import functools
from .user_session import UserSession
import json

SESSION_TYPES = [UserSession]
from .session_repository import SessionsRepository

session_repository = SessionsRepository()


# callback to reload the user object
@login_manager.user_loader
def load_user(userid):
    return session_repository.get_session_by_id(userid)


def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return json.dumps({"success": False, "error": "Unauthorized!"})
        else:
            return f(*args, **kwargs)

    return wrapped
