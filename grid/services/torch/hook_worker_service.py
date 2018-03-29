import json
import random
import re

import torch
from ..base import BaseService
from ...lib import utils, torch_utils as tu
from ... import channels

class HookWorkerService(BaseService):
    def __init__(self, worker):
        super().__init__(worker)
        for tensor_type in self.tensor_types:
            tu.hook_tensor_ser(self, tensor_type)
        tu.hook_var_ser(self)

        # I listen for people to ask me for torch objects
        req_callback = channels.torch_listen_for_obj_req_callback(
            self.worker.id)
        self.worker.listen_to_channel(req_callback, self.receive_obj_request)

        # Listen for torch commands
        comm_callback = channels.torch_listen_for_command_callback(
            self.worker.id)
        self.worker.listen_to_channel(comm_callback, self.handle_command)


    def handle_command(self, message):
        client_id = message['from']
        message, response_channel = utils.unpack(message)
        result, owners = self.process_command(message)
        compiled = json.dumps(self.compile_result(result, owners))
        self.return_result(compiled, response_channel)


    def process_command(self, command_msg):
        args = tu.map_tuple(self, command_msg['args'], tu.retrieve_tensor)
        kwargs = tu.map_dict(self, command_msg['kwargs'], tu.retrieve_tensor)
        has_self = command_msg['has_self']
        # TODO: Implement get_owners and refactor to make it prettier
        combined = list(args) + list(kwargs.values())
        if has_self:
            command = tu.command_guard(command_msg['command'],
                self.tensorvar_methods)
            obj_self = tu.retrieve_tensor(self, command_msg['self'])
            combined = combined + [obj_self]
            command = eval('obj_self.{}'.format(command))
        else:
            command = tu.command_guard(command_msg['command'], self.torch_funcs)
            command = eval('torch.{}'.format(command))
        _, owners = tu.get_owners(combined)
        return command(*args, **kwargs), owners


    def compile_result(self, result, owners):
        try:
            torch_type = result.type()
            result = self.register_object(result, owners=owners)
            registration = dict(id=result.id,
                owners=result.owners, is_pointer=True)
            return {'torch_type':torch_type, 'registration':registration}
        except AttributeError:
            return [self.compile_result(x, owners) for x in result]


    def return_result(self, compiled_result, response_channel):
        return self.worker.publish(
            channel=response_channel, message=compiled_result)


    def receive_obj_request(self, msg):

        obj_id, response_channel = utils.unpack(msg)

        if (obj_id in self.worker.objects.keys()):
            new_owner = re.search('(.+)_[0-9]{1,11}', response_channel).group(1)
            obj = self.register_object(self.worker.objects[obj_id],
                id=obj_id, owners=[new_owner])
            response_str = obj.ser()
        else:
            response_str = 'n/a - tensor not found'

        self.worker.publish(channel=response_channel, message=response_str)