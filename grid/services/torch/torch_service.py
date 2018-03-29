from ..base import BaseService
from .hook_service import HookService
from ... import channels
from ...lib import utils

import torch
from bitcoin import base58

import inspect
import copy
import json


class TorchService(BaseService):
    # this service is responsible for certain things
    # common to both clients and workers
    def __init__(self, worker):
        super().__init__(worker)

        def print_messages(message):
            print(message.keys())
            fr = base58.encode(message['from'])
            print(message['data'])
            print("From:" + fr)
            # return message

        # I listen for people to send me tensors!!
        rec_callback = channels.torch_listen_for_obj_callback(
            self.worker.id)
        self.worker.listen_to_channel(rec_callback, self.receive_obj)


    def receive_obj(self, msg):
        ## The inverse of Tensor.ser (defined in torch_utils.py)
        # TODO: generalize to Variable
        obj_msg = utils.unpack(msg)
        if (type(obj_msg) == str):
            obj_msg = json.loads(obj_msg)
        _tensor_type = obj_msg['torch_type']
        try:
            tensor_type = tu.types_guard(_tensor_type)
        except KeyError:
            raise TypeError(
                "Tried to receive a non-Torch object of type {}.".format(
                    _tensor_type))
        # this could be a significant failure point, security-wise
        if ('data' in msg.keys()):
            data = obj_msg['data']
            data = tu.tensor_contents_guard(data)
            v = tensor_type(data)
        else:
            v = torch.old_zeros(0).type(tensor_type)

        # delete registration from init, cause it's got an incorrect id
        del self.worker.objects[v.id]

        v = self.register_object(v, id=obj_msg['id'])
        return v
