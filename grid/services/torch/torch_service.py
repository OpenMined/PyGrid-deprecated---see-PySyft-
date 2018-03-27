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

        # I listen for people to ask me for tensors!!
        req_callback = channels.torch_listen_for_obj_req_callback(
            self.worker.id)
        self.worker.listen_to_channel(req_callback, self.receive_obj_request)


    def receive_obj(self, msg):
        ## The inverse of Tensor.ser (defined in torch_utils.py)
        # TODO: generalize to Variable
        obj_msg = utils.unpack(msg)
        if (type(obj_msg) == str):
            obj_msg = json.loads(obj_msg)
        _tensor_type = obj_msg['type']
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

        # delete registration just in case we want to override
        del self.worker.objects[v.id]

        v = self.register_object(v, id=obj_msg['id'], owners=v.owners)
        return v


    # TODO: Receive commands needs to be here;
    #       should not depend on any of the torch hooking code;
    #       should be completely general
    def receive_command(self, command):
        if (command['base_type'] == 'torch.FloatTensor'):
            raw_response = torch.FloatTensor.process_command(self, command)

        return json.dumps(raw_response)
