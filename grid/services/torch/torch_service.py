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

    # this service creates everything the client needs to be able to interact
    # with torch on the Grid (it's really awesome, but it's a WIP)

    def __init__(self, worker):
        super().__init__(worker)

        self.worker = worker

        def print_messages(message):
            print(message.keys())
            fr = base58.encode(message['from'])
            print(message['data'])
            print("From:" + fr)
            # return message

        # I listen for people to send me tensors!!
        rec_callback = channels.torch_listen_for_obj_callback(
            self.worker.id)
        self.worker.listen_to_channel(rec_callback,
                                      self.receive_obj)

        # I listen for people to ask me for tensors!!
        req_callback = channels.torch_listen_for_obj_req_callback(
            self.worker.id)
        self.worker.listen_to_channel(req_callback,
                                      self.receive_obj_request)


    def receive_obj(self, msg):
        # TODO: generalize to Variable
        dic = json.loads(msg['data'])
        obj_type = dic['type']
        if obj_type in tensor_types:
            obj = obj_type.de(dic)
            obj.is_pointer = False
            obj.owner = self.worker.id
            self.objects[obj.id] = obj
            return obj
        raise TypeError(
            "Tried to receive a non-Torch object of type {}.".format(
                obj_type))

    # This will be deprecated; send_command in HookService should take over
    #def send_command(self, command, to):
    #    return to.receive_command(command)

    def receive_obj_request(self, msg):

        obj_id, response_channel = json.loads(msg['data'])

        if (obj_id in self.objects.keys()):
            response_str = self.objects[obj_id].ser()
        else:
            response_str = 'n/a - tensor not found'

        self.worker.publish(channel=response_channel, message=response_str)

    # TODO: Receive commands needs to be here;
    #       should not depend on any of the torch hooking code;
    #       should be completely general
    def receive_command(self, command):
        if (command['base_type'] == 'torch.FloatTensor'):
            raw_response = torch.FloatTensor.process_command(self, command)

        return json.dumps(raw_response)
