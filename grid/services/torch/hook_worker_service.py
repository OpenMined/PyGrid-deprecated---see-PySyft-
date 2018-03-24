import torch
from ..base import BaseService
from ..lib import torch_utils as tu


class HookWorkerService(BaseService):
    def __init__(self, worker):
        super().__init__(worker)
        for tensor_type in self.tensor_types:
            tu.hook_tensor_serde(self, tensor_type)
        tu.hook_var_serde(self)

    def process_command(self, command_msg):
        args = tu.map_tuple(self, command_msg['args'], tu.retrieve_tensor)
        kwargs = tu.map_dict(self, command_msg['kwargs'], tu.retrieve_tensor)
        has_self = command_msg['has_self']
        if has_self:
            command = tu.command_guard(command_msg['command'],
                self.tensorvar_methods)
            obj_self = tu.retrieve_tensor(self, command_msg['self'])
            command = eval('obj_self.{}'.format(command))
        else:
            command = tu.command_guard(command_msg['command'], self.torch_funcs)
            command = eval('torch.{}'.format(command))
        return command(*args, **kwargs)

    def return_result(self, result):
        # TODO
        try:
            torch_type = result.type()
        except AttributeError:
            pass
