import torch
from ..base import BaseService
from ... import channels
from ...lib import torch_utils as tu

from collections import OrderedDict
from functools import wraps, partial, partialmethod
import inspect
import random
import re
from types import *


class HookService(BaseService):
    def __init__(self, worker):
        super().__init__(worker)

        # Methods that caused infinite recursion during testing
        # TODO: May want to handle the ones in "exclude" manually at some point
        self.exclude = ['ndimension', 'nelement', 'size','numel']
        # This one wasn't in dir(Variable) -- probably a C thing
        self.var_exclude = ['__getattr__']

        # Perform overloading
        self.hook_torch_module()
        for t_type in self.tensor_types:
            self.hook_tensor(t_type)
        self.hook_variable()
        print('==============')
        print("Overloading complete.")


    ## Registration and communication handlers
    def send_obj(self, obj, recipient):
        self.worker.publish(
            channels.torch_listen_for_obj_callback(recipient),
            message=obj.ser(include_data=True))


    def request_obj(self, obj, sender):
        return self.worker.request_response(
            channel=channels.torch_listen_for_obj_req_callback(sender),
            message=obj.id,
            response_handler=self.worker.services['torch_service'].receive_obj)


    def send_command(self, command, recipient):
        torch_type, registration = self.worker.request_response(
            channels.torch_listen_for_command_callback(recipient),
            message=command,
            response_handler=self.process_response)
        return registration, torch_type


    def assemble_result_pointer(self, registration, torch_type):
        # TODO: extend to iterables of tensor pointers
        result = torch_type(0)
        return self.register_object(result, **registration)


    def process_response(self, response):
        response = utils.unpack(response)
        return response['tensor_type'], response['registration']


    @staticmethod
    def compile_command(partial_func, has_self):
        func = partial_func.func
        args = partial_func.args
        kwargs = partial_func.keywords
        command = {}
        command['has_self'] = has_self
        if has_self:
            command['self'] = args[0]
            args = args[1:]
        command['command'] = func.__name__
        command['args'] = args
        command['kwargs'] = kwargs
        command['arg_types'] = [type(x) for x in args]
        command['kwarg_types'] = [type(kwargs[x]) for x in kwargs]
        return command


    ## Grid-specific method hooking
    def hook_tensor_send(service_self, tensor_type):
        def send_(self, workers):
            workers = tu.check_workers(self, workers) # makes singleton, if needed
            for worker in workers:
                # TODO: sync or async? likely won't be worth doing async,
                #       but should check (low priority)
                service_self.send_obj(self, worker)
            self.set_(tensor_type(0))
            self = service_self.register_object(self,
                is_pointer=True,
                owners=workers)
            return self

        setattr(tensor_type, 'send_', send_)


    def hook_tensor_get(service_self, tensor_type):
        def get_(self, reduce=lambda x: torch.cat(x).mean(0)):
            # reduce is untested
            # TODO: fully generalize this to multiple workers; consider
            #       adding arguments for other tensor ids, e.g. mapping workers
            #       to tensors, and a reduce function (for example, would allow
            #       for built-in gradient averaging when Variable.get is done)
            #       (low priority)
            if service_self.worker.id in self.owners:
                return self
            collected = [service_self.request_obj(self, worker) for worker in self.owners]
            return self.set_(reduce(collected))
        setattr(tensor_type, 'get_', get_)


    # TODO: Variable.send, Variable.get (will need to send/get Variable
    #       registration attributes, handling data and grad tensors properly)
    #       Resolve Issue #148 before attempting


    ## General hooking wrappers
    @staticmethod
    def pass_func_args(func):
        @wraps(func)
        def pass_args(*args, **kwargs):
            return partial(func, *args, **kwargs)
        return pass_args


    def overload_function(self, func):
        @wraps(func)
        def send_to_workers(*args, **kwargs):
            part = func(*args, **kwargs)
            command = self.compile_command(part, has_self = False)
            tensorvars = tu.get_tensorvars(self, command)
            has_remote = tu.check_remote(tensorvars)
            if has_remote:
                multiple_owners, owners = get_owners(tensorvars)
                if multiple_owners:
                    raise NotImplementedError("""MPC not yet implemented: 
                    Torch objects need to be on the same machine in order
                    to compute with them.""")
                else:
                    for worker in owners:
                        print("Placeholder print for sending command to worker {}".format(worker))
                        registration, torch_type = self.send_command(command, worker)
                        pointer = self.assemble_result_pointer(registration,
                            torch_type)
                    return pointer
            else:
                result = part.func(*args, **kwargs)
                if type(result) in self.tensorvar_types:
                    result = self.register_object(result, is_pointer=False)
                return result
                
        return send_to_workers


    @staticmethod
    def pass_method_args(method):
        @wraps(method)
        def pass_args(*args, **kwargs):
            return partialmethod(method, *args, **kwargs)
        return pass_args


    def overload_method(service_self, method):
        @wraps(method)
        def send_to_workers(self, *args, **kwargs):
            part = method(self, *args, **kwargs)
            if self.is_pointer:
                command = service_self.compile_command(part, has_self=True)
                tensorvars = tu.get_tensorvars(service_self, command)
                has_remote = tu.check_remote(tensorvars)
                multiple_owners, owners = tu.get_owners(tensorvars)
                if has_remote and not multiple_owners:
                    for worker in owners:
                        registration, torch_type = service_self.send_command(
                            command, worker)
                        # only returns last pointer, since tensors will
                        # be identical across machines for right now
                        pointer = service_self.assemble_result_pointer(
                            registration, torch_type)
                else:
                    raise NotImplementedError("""MPC not yet implemented:
                        Torch objects need to be on the same machine in
                        order to compute with them.""")
                return pointer
            else:
                result = part.func(self, *args, **kwargs)
                if (type(result) in service_self.tensorvar_types and 
                    not hasattr(result, 'owner')):
                    result = service_self.register_object(result,
                        is_pointer=False)
                return result
        return send_to_workers


    ## Special Tensor method hooks
    def hook_tensor___init__(service_self, tensor_type):
        def new___init__(self, *args):
            super(tensor_type, self).__init__()
            self = service_self.register_object(self, is_pointer=False)

        tensor_type.__init__ = new___init__
    

    def hook_tensor___new__(service_self, tensor_type):
        tensor_type.old___new__ = tensor_type.__new__
        def new___new__(cls, *args, **kwargs):
            result = cls.old___new__(cls, *args,  **kwargs)
            result = service_self.register_object(result, is_pointer=False)
            return result
        
        tensor_type.__new__ = new___new__


    def hook_tensor___repr__(service_self, tensor_type):
        tensor_type.old__repr__ = tensor_type.__repr__
        def new___repr__(self):
            if service_self.worker.id in self.owners:
                return self.old__repr__()
            else:
                return "[{}.{} - Locations:{}]".format(
                    tensor_type.__module__,
                    tensor_type.__name__,
                    self.owners)

        tensor_type.__repr__ = new___repr__


    ## Special Variable method hooks
    def hook_var___new__(service_self):
        torch.autograd.variable.Variable.old___new__ = torch.autograd.variable.Variable.__new__
        def new___new__(cls, *args, **kwargs):
            result = cls.old___new__(cls, *args,  **kwargs)
            result = service_self.register_object(result, is_pointer=False)
            return result
        
        torch.autograd.variable.Variable.__new__ = new___new__


    def hook_var_contents(service_self):
        torch.autograd.variable.Variable.old_data = torch.autograd.variable.Variable.data
        torch.autograd.variable.Variable.old_grad = torch.autograd.variable.Variable.grad
        @property
        def new_data(self):
            try:
                self.data_registered
            except AttributeError:
                self.old_data = service_self.register_object(
                    self.old_data, id=self.id,
                    owners=self.owners, is_pointer=self.is_pointer)
                self.data_registered = True
            return self.old_data
        
        @property
        def new_grad(self):
            try:
                self.grad_registered
            except AttributeError:
                if self.old_grad is not None:
                    self.old_grad = service_self.register_object(
                        self.old_grad, id=self.id,
                    owners=self.owners, is_pointer=self.is_pointer)
                    self.grad_registered = True
            return self.old_grad
        
        torch.autograd.variable.Variable.data = new_data
        torch.autograd.variable.Variable.grad = new_grad


    ## Overloading Torch objects
    def hook_torch_module(self):
        print('Overloading Torch module')
        for attr in self.torch_funcs:
            if attr == 'typename':
                continue
            lit = getattr(torch, attr)
            if (type(lit) in [FunctionType, BuiltinFunctionType]):
                passer = self.pass_func_args(lit)
                new_attr = self.overload_function(passer)
                setattr(torch, attr, new_attr)


    def hook_tensor(self, tensor_type):
        print('Overloading {}'.format(tensor_type.__name__))
        self.hook_tensor___init__(tensor_type)
        self.hook_tensor___new__(tensor_type)
        self.hook_tensor___repr__(tensor_type)
        self.hook_tensor_send(tensor_type)
        self.hook_tensor_get(tensor_type)
        #tu.hook_tensor_serde(tensor_type) # currently unfinished
        for attr in dir(tensor_type):
            if attr in self.exclude:
                continue
            lit = getattr(tensor_type, attr)
            is_base = attr in dir(object)
            is_desc = inspect.ismethoddescriptor(lit)
            is_func = type(lit)==FunctionType
            try:
                is_service_func = 'HookService' in lit.__qualname__
            except:
                is_service_func = False
            is_old = re.match('old*', attr) is not None
            if ((is_desc or (is_func and not is_service_func)) 
                and not is_base and not is_old):
                passer = self.pass_method_args(lit)
                new_attr = self.overload_method(passer)
                setattr(tensor_type, 'old_{}'.format(attr), lit)
                setattr(tensor_type, attr, new_attr)


    def hook_variable(self):
        print('Overloading Variable')
        self.hook_var___new__()
        self.hook_var_contents()
        for attr in dir(torch.autograd.variable.Variable):
            if attr in self.exclude + self.var_exclude:
                continue
            lit = getattr(torch.autograd.variable.Variable, attr)
            is_base = attr in dir(object)
            is_desc = inspect.ismethoddescriptor(lit)
            is_func = type(lit)==FunctionType
            try:
                is_service_func = 'HookService' in lit.__qualname__
            except:
                is_service_func = False
            is_old = re.match('old*', attr) is not None
            if ((is_desc or (is_func and not is_service_func)) 
                and not is_base and not is_old):
                passer = self.pass_method_args(lit)
                new_attr = self.overload_method(passer)
                setattr(torch.autograd.variable.Variable, 
                    'old_{}'.format(attr), lit)
                setattr(torch.autograd.variable.Variable, attr, new_attr)
