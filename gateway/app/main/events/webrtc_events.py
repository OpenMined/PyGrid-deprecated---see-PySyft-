import json
from ..scopes import scopes
from ..codes import GRID_MSG

def join_room(message: dict) -> str:
    data = message[GRID_MSG.DATA_FIELD]
    try:
        scope_id = data.get("scopeId", None)
        scope = scopes.get_scope(scope_id)

        # for worker in scope.assignments.keys():
        #   if worker != worker_id:
        #      session = get_session(worker_id)
        #      session.send(json.dumps(message))
        return ""
    except Exception as e:
        return str(e)


def internal_message(message: dict) -> str:
    return ""


def peer_left(message: dict) -> str:
    return ""
