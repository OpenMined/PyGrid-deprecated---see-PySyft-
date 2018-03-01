from ... import channels
from ..base import BaseService

class ListenForTorchObjectsService(BaseService):

    # this service just listens on the general "openmined" channel so that other nodes
    # on the network know its there.

    def __init__(self,worker):
        super().__init__(worker)

        self.worker = worker

        def print_messages(message):
            fr = base58.encode(message['from'])
            print(fr)
            print(message['data'])
            return message


        listen_for_callback_channel = channels.torch_listen_for_obj_callback(self.worker.id)
        self.worker.listen_to_channel(listen_for_callback_channel,print_messages)
