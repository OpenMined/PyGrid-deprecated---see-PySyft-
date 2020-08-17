from syft.core.node.abstract.node import AbstractNode

from typing import Union
from syft.core.common.message import (
    SyftMessage,
    EventualSyftMessageWithoutReply,
    ImmediateSyftMessageWithoutReply,
    ImmediateSyftMessageWithReply,
    SignedMessage,
)


class EventHandler(object):
    def __init__(self, node: AbstractNode):
        self.node = node

    def process(self, msg: SyftMessage) -> Union[SyftMessage, None]:
        # Immediate message with reply
        if isinstance(msg, ImmediateSyftMessageWithReply):
            reply = self.node.recv_immediate_msg_with_reply(msg=msg)
            return reply

        # Immediate message without reply
        elif isinstance(msg, ImmediateSyftMessageWithoutReply):
            self.node.recv_immediate_msg_without_reply(msg=msg)

        # Eventual message without reply
        else:
            self.node.recv_eventual_msg_without_reply(msg=msg)
