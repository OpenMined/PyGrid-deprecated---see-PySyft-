import json
from ..scopes import scopes
from ..codes import GRID_MSG
from .socket_handler import SocketHandler

handler = SocketHandler()


def scope_broadcast(message: dict, socket) -> str:
    data = message[GRID_MSG.DATA_FIELD]
    try:
        scope_id = data.get("scopeId", None)
        worker_id = data.get("workerId", None)
        scope = scopes.get_scope(scope_id)
        for worker in scope.assignments.keys():
            if worker != worker_id:
                handler.send_msg(worker, json.dumps(message))
        return ""
    except Exception as e:
        return str(e)


def internal_message(message: dict, socket) -> str:
    data = message[GRID_MSG.DATA_FIELD]
    try:
        destination = data.get("to", None)
        if destination:
            handler.send_msg(destination, json.dumps(message))
        return ""
    except Exception as e:
        return str(e)
