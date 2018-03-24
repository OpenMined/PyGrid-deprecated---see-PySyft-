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
        # TODO: Handle the ones in "exclude" manually at some point
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
            message=obj.ser())

    def request_obj(self, obj):
        return self.worker.request_response(
            channel=channels.torch_listen_for_obj_req_callback(obj.owner),
            message=obj.id,
            response_handler=self.worker.services['torch_service'].receive_obj)

    # TODO: See Issue #131
    def send_command(self, command, recipient):
        #self.worker.publish() # finish this
        print(command['command'])
        print([type(arg) for arg in command['args']])
        print([type(pair) for pair in command['kwargs']])
        print('===========')
        print()
        # TODO: fix up after IPFS is integrated
        # torch_type, registration = ???
        torch_type = torch.FloatTensor
        registration = dict(id=random.randint(0, 1e10),
            owners=['other_worker'],
            is_pointer=True)
        return registration, torch_type

    def assemble_result(self, registration, torch_type):
        result = torch_type(0)
        return self.register_object(result, **registration)

    # TODO: inputs the response of a remote computation,
    #       outputs it's registration(s) and it's torch_type(s)
    # TODO: Allow for multiple tensor pointers
    #       (e.g. torch.split should return a sequence of pointers)
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

    # TODO: See Issue #131
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
            workers = tu.check_workers(workers) # makes singleton, if needed
            for worker in workers:
                # TODO: actually generalize this to multiple workers
                #       in the hooking wrappers
                # TODO: sync or async? likely won't be worth doing async,
                #       but should check (low priority)
                service_self.send_obj(self, worker)
            self.is_pointer = True
            self.owners = workers
            self.set_(tensor_type(0))
            return self

        setattr(tensor_type, 'send_', send_)

    def hook_tensor_get(service_self, tensor_type):
        def get_(self, reduce=lambda x: torch.cat(x).mean(0)):
            # reduce is untested
            # TODO: actually generalize this to multiple workers; consider
            #       adding arguments for other tensor ids, e.g. mapping workers
            #       to tensors, and a reduce function (for example, would allow
            #       for built in gradient averaging when Variable.get is done)
            #       (low priority)
            if service_self.worker.id in self.owners:
                return self
            collected = [service_self.request_obj(self, worker) for worker in self.owners]
            return self.set_(reduce(collected))

        setattr(tensor_type, 'get_', get_)

    # TODO: Remove, this is just a reference for implementing in lib/torch_utils.py
    def hook_float_tensor_serde(self):
        def ser(self, include_data=True):

            msg = {}
            msg['type'] = 'torch.FloatTensor'
            if (include_data):
                msg['data'] = self.tolist()
            msg['id'] = self.id
            msg['owner'] = self.owner

            return json.dumps(msg)

        def de(msg):
            if (type(msg) == str):
                msg = json.loads(msg)

            if ('data' in msg.keys()):
                v = torch.FloatTensor(msg['data'])
            else:
                v = torch.zeros(0)

            del self.worker.objects[v.id]

            if (msg['id'] in self.worker.objects.keys()):
                v_orig = self.worker.objects[msg['id']].set_(v)
                return v_orig
            else:
                self.worker.objects[msg['id']] = v
                v.id = msg['id']
                v.owner = msg['owner']
                return v

        torch.FloatTensor.ser = ser
        torch.FloatTensor.de = de

    # TODO: Generalize a ton; see Issue #129; use torch_funcs and 
    #       tensorvar_methods class attributes
    # TODO: need to send resulting json back so that receive_commands 
    #       in torch_utils.py can unpack properly
    #       (highly related to Issue #130)
    def hook_float_tensor_process_command(self):
        def process_command(worker, command):
            if (command['command'] == 'add'):
                a = worker.objects[int(command['values'][0])]
                b = worker.objects[int(command['values'][1])]
                c = a.add(b)
                return [c.ser(False)]
            else:
                return "command not found"

        torch.FloatTensor.process_command = process_command

    # TODO: Variable.send, Variable.get (will need to send/get Variable
    #       registration attributes, as well as data and grad tensors)
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
            has_remote, multiple_owners, owners = tu.check_tensorvars(tensorvars)
            if not has_remote:
                result = part.func(*args, **kwargs)
                if type(result) in self.tensorvar_types:
                    result = self.register_object(result, is_pointer=False)
                return result
            # when the api is generalized to function on multiple workers,
            # the following two cases should be consolidated
            elif multiple_owners:
                raise NotImplementedError("""MPC not yet implemented: 
                    Torch objects need to be on the same machine in order
                    to compute with them.""")
            else:
                for worker in owners:
                    print("Placeholder print for sending command to worker {}".format(worker))
                    registration, torch_type = self.send_command(command, worker)
                    pointer = self.assemble_result(registration, torch_type)
                return pointer
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
                has_remote, multiple_owners, owners = tu.check_tensorvars(tensorvars)
                if has_remote and not multiple_owners:
                    for worker in owners: # Right now, this can only be singleton
                        print("""Placeholder print for sending command to worker {}""".format(worker))
                        registration, torch_type = service_self.send_command(command, worker)
                        pointer = service_self.assemble_result(registration, torch_type)
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
                    self.old_data, is_pointer=False)
                self.data_registered = True
            return self.old_data
        
        @property
        def new_grad(self):
            try:
                self.grad_registered
            except AttributeError:
                if self.old_grad is not None:
                    self.old_grad = service_self.register_object(
                        self.old_grad, is_pointer=False)
                    self.grad_registered = True
            return self.old_grad
        
        torch.autograd.variable.Variable.data = new_data
        torch.autograd.variable.Variable.grad = new_grad


    ## Overloading Torch objects

    # TODO: Issue #132 undo dependency on worker_ids -- no point wasting
    #       time integrating worker_ids into the rest if we're going to
    #       rewrite that part anyway (and we definitely need to rewrite that)

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
