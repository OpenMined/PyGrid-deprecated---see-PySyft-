import os
import json
import re

from pathlib import Path

from .. import channels

from . import utils
# from .shared_variable import SharedVariable
import torch


# Helpers for HookService and TorchService
def check_workers(self, workers):
    if type(workers) is str:
        workers = [workers]
    elif not hasattr(workers, '__iter__'):
        raise TypeError(
            """Can only send {} to a string worker ID or an iterable of
            string worker IDs, not {}""".format(self.__name__, type(owners))
        )
    return workers


def get_tensorvars(self, command):
    args = command['args']
    kwargs = command['kwargs']
    arg_types = command['arg_types']
    kwarg_types = command['kwarg_types']
    tensorvar_args = [args[i] for i in range(
        len(args)) if arg_types[i] in self.tensorvar_types_strs]
    tensorvar_kwvals = [kwargs[i][1] for i in range(
        len(kwargs)) if kwarg_types[i] in self.tensorvar_types_strs]
    return tensorvar_args + tensorvar_kwvals


def check_remote(tensorvars):
    return any([tensorvar.is_pointer for tensorvar in tensorvars])


def get_owners(tensorvars):
    owners = list(set([owner
                       for tensorvar in tensorvars
                       for owner in tensorvar.owners]))
    multiple_owners = len(owners) > 1
    return multiple_owners, owners


def replace_tensorvar(x):
    if hasattr(torch, 'old_is_tensor'):
        check = torch.old_is_tensor
    else:
        check = torch.is_tensor
    try:
        if check(x) or isinstance(x, torch.autograd.Variable):
            return '_fl.{}'.format(x.id)
        else:
            [replace_tensorvar(i) for i in x]
    except (AttributeError, TypeError):
        return x


def replace_in_command(command_msg):
    command_msg['args'] = map_tuple(
        None, command_msg['args'], replace_tensorvar)
    command_msg['kwargs'] = map_dict(
        None, command_msg['kwargs'], replace_tensorvar)
    try:
        command_msg['self'] = replace_tensorvar(command_msg['self'])
    except KeyError:
        pass
    return command_msg

# Client needs to identify a tensor before sending commands that use it


def id_tensorvar(x):
    pat = re.compile('_fl.(.*)')
    try:
        if isinstance(x, str):
            return int(pat.search(x).group(1))
        else:
            return [id_tensorvar(i) for i in x]
    except AttributeError:
        return x


# Safety checks for serializing and deserializing torch objects
# Desperately needs stress testing before going out in the wild
map_tensor_type = {
    'torch.FloatTensor': torch.FloatTensor,
    'torch.DoubleTensor': torch.DoubleTensor,
    'torch.HalfTensor': torch.HalfTensor,
    'torch.ByteTensor': torch.ByteTensor,
    'torch.CharTensor': torch.CharTensor,
    'torch.ShortTensor': torch.ShortTensor,
    'torch.IntTensor': torch.IntTensor,
    'torch.LongTensor': torch.LongTensor
}
map_var_type = {
    'torch.autograd.variable.Variable': torch.autograd.variable.Variable,
    # 'torch.nn.parameter.Parameter': torch.nn.parameter.Parameter,
    'torch.nn.parameter.Parameter': torch.nn.parameter.Parameter
    # 'SharedVariable': SharedVariable
}
map_torch_type = dict(map_tensor_type, **map_var_type)


def types_guard(obj_msg):
    _torch_type = obj_msg['torch_type']
    try:
        return map_torch_type[_torch_type]
    except KeyError:
        raise TypeError(
            "Tried to receive a non-Torch object of type {}.".format(
                _torch_type))


def tensor_contents_guard(contents):
    # TODO: check to make sure the incoming list isn't dangerous to use for
    #       constructing a tensor (likely non-trivial)
    return contents


def command_guard(command, allowed):
    if command not in allowed:
        raise RuntimeError(
            'Command "{}" is not a supported Torch operation.'.format(command))
    return command


# Worker needs to retrieve tensor by ID before computing with it
def retrieve_tensor(self, x):
    try:
        return self.worker.objects[id_tensorvar(x)]
    except TypeError:
        try:
            return [self.worker.objects[i] for i in id_tensorvar(x)]
        except TypeError:
            return x
    except KeyError:
        return x


def map_tuple(service, args, func):
    if service:
        return tuple(func(service, x) for x in args)
    else:
        return tuple(func(x) for x in args)


def map_dict(service, kwargs, func):
    if service:
        return {key: func(service, val) for key, val in kwargs.items()}
    else:
        return {key: func(val) for key, val in kwargs.items()}


def send_obj(service, obj, recipient):
        """Send Torch object to recipient."""
        service.worker.publish(
            channels.torch_listen_for_obj_callback(recipient),
            message=obj._ser())


def hook_tensor__ser(service_self, tensor_type):
    def _ser(self, include_data=True):
        """Serializes a {} object to JSON.""".format(tensor_type)
        tensor_msg = {}
        tensor_msg['torch_type'] = self.type()
        if include_data:
            tensor_msg['data'] = self.tolist()
        tensor_msg['id'] = self.id
        tensor_msg['owners'] = self.owners
        tensor_msg['is_pointer'] = not include_data
        return json.dumps(tensor_msg)

    tensor_type._ser = _ser


def hook_var__ser(service_self):
    def _ser(self, include_data=True):
        var_msg = {}
        var_msg['torch_type'] = re.search("<class '(.*)'>",
                                          str(self.__class__)).group(1)
        var_msg['requires_grad'] = self.requires_grad
        var_msg['volatile'] = self.volatile
        var_msg['data'] = self.data._ser(include_data)
        if self.grad is not None:
            var_msg['grad'] = self.grad._ser(include_data)
        else:
            var_msg['grad'] = None
        var_msg['id'] = self.id
        var_msg['owners'] = self.owners
        var_msg['is_pointer'] = not include_data
        return json.dumps(var_msg)

    torch.autograd.variable.Variable._ser = _ser


def hook_tensor_send_(service_self, tensor_type):
    def send_(self, workers):
        """
        Sends a Tensor object to a (sequence of) Grid workers.

        Args:
        workers: string (or sequence) containing IPFS address(es)
            of worker node(s).
        """
        workers = check_workers(
            self, workers)  # makes singleton, if needed
        self = service_self.register_object_(
            self, id=self.id, owners=workers)
        for worker in workers:
            # TODO: sync or async? likely won't be worth doing async,
            #       but should check (low priority)
            send_obj(service_self, self, worker)
        self = service_self.register_object_(self.old_set_(tensor_type(0)),
                                             id=self.id, owners=workers,
                                             is_pointer=True)
        return self

    setattr(tensor_type, 'send_', send_)


def hook_var_send_(service_self):
    def send_(self, workers):
        """
        Sends a Variable object to a (sequence of) Grid workers.

        Args:
        workers: string (or sequence) containing IPFS address(es)
            of worker node(s).
        """
        workers = check_workers(
            self, workers)  # makes singleton, if needed
        self = service_self.register_object_(
            self, id=self.id, owners=workers)
        for worker in workers:
            # TODO: sync or async? likely won't be worth doing async,
            #       but should check (low priority)
            send_obj(service_self, self, worker)
        service_self.register_object_(self, id=self.id,
                                      owners=self.owners, is_pointer=True)

        return var_to_pointer(service_self, self)

    setattr(torch.autograd.variable.Variable, 'send_', send_)


def var_to_pointer(service, var):
    if var.grad is not None:
        var_to_pointer(service, var.grad)

    var.data.old_set_(var.data.__class__(0))
    service.register_object_(var.data, id=var.data.id, owners=var.owners,
                          is_pointer=True)

    return var


def hook_get_(service_self, torch_type):
    def get_(self, reduce=lambda x: x[0]):
        """
        Gets a Torch object from its current owners.

        Args:
        reduce: (EXPERIMENTAL) How to reduce tensors that come from
            multiple workers
        """
        # TODO: fully generalize this to multiple workers; consider
        #       adding arguments for other tensor ids, e.g. mapping workers
        #       to tensors, and a reduce function (for example, would allow
        #       for built-in gradient averaging when Variable.get is done)
        #       (low priority)
        if service_self.worker.id in self.owners:
            return self
        collected = []
        for worker in self.owners:
            x = service_self.request_obj(self, worker)
            collected.append(service_self.register_object_(x, id=x.id))
        return service_self.register_object_(self.old_set_(reduce(collected)),
                                                id=self.id)
    setattr(torch_type, 'get_', get_)