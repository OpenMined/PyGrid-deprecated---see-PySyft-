import torch
from ..base import BaseService
from ..lib import torch_utils as tu


class HookWorkerService(BaseService):
    def __init__(self, worker):
        super().__init__(worker)
        for tensor_type in self.tensor_types:
            tu.hook_tensor_ser(self, tensor_type)
        tu.hook_var_ser(self)

        # Listen for command
        comm_callback = channels.torch_listen_for_command_callback(
            self.worker.id)
        self.worker.listen_to_channel(comm_callback, self.handle_command)


    def handle_command(self, message):
        client_id = message['from']
        message = utils.unpack(message)
        result = self.process_command(message)
        compiled = json.dumps(self.compile_result(result))
        self.return_result(compiled, client_id)


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


    def compile_result(self, result):
        # TODO: need to test this
        try:
            torch_type = result.type()
            registration = dict(id=random.randint(0, 1e10),
                owners=[self.worker.id], is_pointer=True)
            return {'torch_type':torch_type, 'registration':registration}
        except AttributeError:
            return [compile_result(x) for x in result]


    def return_result(self, compiled_result, client_id):
        return self.worker.publish(
            channels.torch_listen_for_command_response_callback(client_id),
            message=compiled_result)


    def receive_obj_request(self, msg):

        obj_id, response_channel = utils.unpack(msg)

        if (obj_id in self.worker.objects.keys()):
            response_str = self.worker.objects[obj_id].ser()
        else:
            response_str = 'n/a - tensor not found'

        self.worker.publish(channel=response_channel, message=response_str)