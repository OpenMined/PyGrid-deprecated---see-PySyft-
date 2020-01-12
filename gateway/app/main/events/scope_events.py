from ..codes import GRID_MSG
from ..scopes import scopes
import uuid
import json


def get_protocol(message: dict) -> str:
    data = message[GRID_MSG.DATA_FIELD]
    try:
        worker_id = data.get("workerId", None)
        scope_id = data.get("scopeId", None)
        protocol_id = data.get("protocolId", None)

        if not worker_id:
            # Create a new worker ID / Attach this ID on this ws connection.
            worker_id = str(uuid.uuid4())

        if not scope_id:
            # Create new scope.
            scope = scopes.create_scope(worker_id, protocol_id)
            scope_id = scope.id
        else:
            scope = scopes.get_scope(scope_id)

        scope.add_participant(worker_id)

        # Returns:
        data = dict()
        data["user"] = {
            "workerId": worker_id,
            "scopeId": scope_id,
            "protocolId": scope.protocol,
            "role": scope.get_role(worker_id),
            "plan": scope.plan_number(worker_id),
            "assignment": scope.get_assignment(worker_id),
        }

        data["participants"] = {
            p: scope.get_assignment(p) for p in scope.get_participants()
        }

        response = {"type": GRID_MSG.GET_PROTOCOL, "data": data}

        return json.dumps(response)
    except Exception as e:
        return str(e)
