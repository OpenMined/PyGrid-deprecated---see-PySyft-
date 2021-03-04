# stdlib
import secrets
from typing import List
from typing import Type
from typing import Union

# third party
from nacl.signing import VerifyKey
from nacl.encoding import HexEncoder

# syft relative
from syft.core.node.abstract.node import AbstractNode
from syft.core.node.common.service.auth import service_auth
from syft.core.node.common.service.node_service import ImmediateNodeServiceWithReply
from syft.core.node.common.service.node_service import ImmediateNodeServiceWithoutReply
from syft.core.common.message import ImmediateSyftMessageWithReply
from syft.core.common.serde.deserialize import _deserialize
from syft.proto.core.io.address_pb2 import Address as Address_PB
from syft.core.common.uid import UID

from syft.grid.messages.transfer_messages import (
    LoadObjectMessage,
    LoadObjectResponse,
    SaveObjectMessage,
    SaveObjectResponse,
)


def create_initial_setup(
    msg: LoadObjectMessage,
    node: AbstractNode,
    verify_key: VerifyKey,
) -> LoadObjectResponse:
    _worker_address = msg.content.get("address", None)
    _obj_id = msg.content.get("uid", None)
    _searchable = msg.content.get("searchable", False)
    _current_user_id = msg.content.get("current_user", None)

    users = node.users

    if not _current_user_id:
        _current_user_id = users.first(
            verify_key=verify_key.encode(encoder=HexEncoder).decode("utf-8")
        ).id

    __allowed = users.can_edit_roles(user_id=_current_user_id)

    addr_pb = Address_PB()
    addr_pb.ParseFromString(_worker_address.encode("ISO-8859-1"))
    _syft_address = _deserialize(blob=addr_pb)

    _syft_id = UID.from_string(value=_obj_id)

    _worker_client = node.in_memory_client_registry[_syft_address.domain_id]

    try:
        _obj = node.store[_syft_id]
    except Exception:
        raise Exception("Object Not Found!")

    _obj.data.send(_worker_client, searchable=_searchable)

    return LoadObjectResponse(
        address=msg.reply_to,
        status_code=200,
        content={"msg": "Object loaded successfully!"},
    )


def get_setup(
    msg: SaveObjectMessage,
    node: AbstractNode,
    verify_key: VerifyKey,
) -> SaveObjectResponse:
    try:
        return SaveObjectResponse(
            address=msg.reply_to,
            status_code=200,
            content={"setup": node.setup_configs},
        )
    except Exception as e:
        return SaveObjectResponse(
            address=msg.reply_to,
            success=False,
            content={"error": str(e)},
        )


class TransferObjectService(ImmediateNodeServiceWithReply):

    msg_handler_map = {
        LoadObjectMessage: create_initial_setup,
        SaveObjectMessage: get_setup,
    }

    @staticmethod
    @service_auth(guests_welcome=True)
    def process(
        node: AbstractNode,
        msg: Union[
            LoadObjectMessage,
            SaveObjectMessage,
        ],
        verify_key: VerifyKey,
    ) -> Union[LoadObjectResponse, SaveObjectResponse,]:
        try:
            return TransferObjectService.msg_handler_map[type(msg)](
                msg=msg, node=node, verify_key=verify_key
            )
        except Exception as e:
            print("n\n\n\ My Exception: \n\n", str(e))

    @staticmethod
    def message_handler_types() -> List[Type[ImmediateSyftMessageWithReply]]:
        return [
            LoadObjectMessage,
            SaveObjectMessage,
        ]
