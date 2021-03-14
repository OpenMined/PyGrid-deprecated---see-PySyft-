from .blueprint import root_blueprint as root_route
from ...core.node import get_node

# syft absolute
from syft.core.common.message import SignedImmediateSyftMessageWithReply
from syft.core.common.message import SignedImmediateSyftMessageWithoutReply

from syft.core.common.serde.deserialize import _deserialize
from syft import serialize
from syft.core.common.serde.serialize import _serialize
from syft import deserialize

from flask import request, Response
import json
from nacl.encoding import HexEncoder

executor_running = False


@root_route.route("/metadata", methods=["GET"])
def metadata_route():
    response_body = {
        "metadata": serialize(get_node().get_metadata_for_client())
        .SerializeToString()
        .decode("ISO-8859-1"),
    }
    return Response(json.dumps(response_body), status=200, mimetype="application/json")


@root_route.route("/pysyft", methods=["POST"])
def root_route():
    data = request.get_data()
    obj_msg = deserialize(blob=data, from_bytes=True)
    if isinstance(obj_msg, SignedImmediateSyftMessageWithReply):
        reply = get_node().recv_immediate_msg_with_reply(msg=obj_msg)
        r = Response(response=_serialize(obj=reply, to_bytes=True), status=200)
        r.headers["Content-Type"] = "application/octet-stream"
        return r
    elif isinstance(obj_msg, SignedImmediateSyftMessageWithoutReply):
        get_node().recv_immediate_msg_without_reply(msg=obj_msg)
    else:
        get_node().recv_eventual_msg_without_reply(msg=obj_msg)
    return ""
