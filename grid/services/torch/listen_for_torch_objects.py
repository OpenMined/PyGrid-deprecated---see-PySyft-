from ... import channels
from ..base import BaseService

class ListenForTorchObjectsService(BaseService):

    # this service just listens on the general "openmined" channel so that other nodes
    # on the network know its there.

    def __init__(self,torch_worker):
        super().__init__(torch_worker)

        self.torch_worker = torch_worker

        def print_messages(message):
            print(message)

        self.listen_to_channel(channels.torch_listen_for_obj_callback(self.id),print_messages)