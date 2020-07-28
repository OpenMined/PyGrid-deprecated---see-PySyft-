from .. import http
from ..events.socket_handler import SocketHandler
from ..codes import MSG_FIELD
from flask import Response
import json

socket_handler = SocketHandler()


@http.route("/node/<id>")
def node_infos(id):
    """Return a response object containing the information of a node with a
    given ID."""
    try:
        worker = socket_handler.get(id)
        response = {}

        if worker:
            response["id"] = worker._id
            response["status"] = worker.status
            response["address"] = worker.address
            response["nodes"] = worker.connected_nodes
            response["datasets"] = worker.hosted_datasets
            response["models"] = list(worker.hosted_models.keys())
            response["cpu"] = worker.cpu_percent
            response["memory"] = worker.mem_usage

            response_body = json.dumps(response)
            return Response(response_body, status=200, mimetype="application/json")
        else:
            return Response(
                {
                    MSG_FIELD.STATUS: MSG_FIELD.ERROR,
                    MSG_FIELD.CONTENT: "Worker ID not found!",
                },
                status=404,
                mimetype="application/json",
            )
    except Exception:
        return Response({}, status=500, mimetype="application/json")
