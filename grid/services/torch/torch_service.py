from ..base import BaseService
from .hook_service import HookService
from ... import channels
from ...lib import utils

import torch
from bitcoin import base58

import inspect
import random
import copy
import json


class TorchService(HookService):

    # this service creates everything the client needs to be able to interact
    # with torch on the Grid (it's really awesome, but it's a WIP)

    def __init__(self, worker):
        super().__init__(worker)

        self.worker = worker

        # TODO: call overload methods from HookService once they're there
        worker_ids = ['A1','A2','B1'] # This will be gone soon
        self.hook_torch_module(worker_ids)
        for t_type in self.tensor_types:
            self.hook_tensor(t_type, worker_ids)
        self.hook_variable(worker_ids)
        print('==============')
        print("Overloading complete.")

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

    # This will be deprecated; receive_commands in HookService should take over
    def receive_command(self, command):
        if (command['base_type'] == 'torch.FloatTensor'):
            raw_response = torch.FloatTensor.process_command(self, command)

        return json.dumps(raw_response)

    # This will likely also be deprecated if it's needed in HookService;
    # otherwise, will need to be rewritten to adapt to the other changes
    def process_response(self, response):
        response = json.loads(response)
        tensor_ids = response
        out_tensors = list()
        for raw_msg in tensor_ids:
            msg = json.loads(raw_msg)
            if (msg["type"] == "torch.FloatTensor"):
                obj = torch.FloatTensor.de(msg)
            out_tensors.append(obj)

        if (len(out_tensors) > 1):
            return out_tensors
        elif (len(out_tensors) == 1):
            return out_tensors[0]
        else:
            return None
