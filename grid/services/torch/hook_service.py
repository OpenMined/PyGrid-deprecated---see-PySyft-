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
        self.objects = {}

        self.tensor_types = [torch.FloatTensor,
                torch.DoubleTensor,
                torch.HalfTensor,
                torch.ByteTensor,
                torch.CharTensor,
                torch.ShortTensor,
                torch.IntTensor,
                torch.LongTensor]
        self.var_types = [torch.autograd.variable.Variable,
                    torch.nn.parameter.Parameter]
        self.tensorvar_types = self.tensor_types + self.var_types

        # Any commands that don't appear in the following lists will not execute
        self.torch_funcs = dir(torch)
        # Consider changing this to a dictionary with lists of methods
        # for each type in tensorvar_types
        self.tensorvar_methods = list(
            set(
                [method
                    for tensorvar in self.tensorvar_types
                    for method in dir(tensorvar)]
                )
            )

        # Methods that caused infinite recursion during testing
        # TODO: Handle the ones in "exclude" manually at some point
        self.exclude = ['ndimension', 'nelement', 'size','numel']
        # This one wasn't in dir(Variable) -- probably a C thing
        self.var_exclude = ['__getattr__'] 


    ## Registration and communication handlers

    def register_object(self, obj, is_pointer_to_remote):
        # TODO: Assign id more intelligently (low priority)
        #       Consider popping id from long list of unique integers
        obj.id = random.randint(0, 1e10)
        obj.owners = [self.worker.id]
        obj.is_pointer_to_remote = is_pointer_to_remote
        self.objects[obj.id] = obj
        return obj

    def send_obj(self, obj, recipient):
        self.worker.publish(
            channels.torch_listen_for_obj_callback(recipient),
            message=obj.ser())

    def request_obj(self, obj):
        return self.worker.request_response(
            channel=channels.torch_listen_for_obj_req_callback(obj.owner),
            message=obj.id,
            response_handler=self.receive_obj)

    def receive_obj(self, msg):
        # TODO: generalize to Variable
        dic = json.loads(msg['data'])
        obj_type = dic['type']
        if obj_type in tensor_types:
            obj = obj_type.de(dic)
            obj.is_pointer_to_remote = False
            obj.owner = self.worker.id
            self.objects[obj.id] = obj
            return obj
        raise TypeError("Tried receiving a non-Torch object")

    # TODO: See Issue #131
    def send_command(self, command, recipient):
        self.worker.publish()
        print(command['command'])
        print([type(arg) for arg in command['args']])
        print([type(pair) for pair in command['kwargs']])
        print('===========')
        print()
        return registration_attrs

    # TODO: See Issue #131
    def receive_commands(worker_ids):
        print("""Placeholder print for receiving commands from workers
            in the following list:""")
        print(worker_ids)

    # TODO: See Issue #131
    @staticmethod
    def compile_command(partial_func, has_self):
        func = partial_func.func
        args = partial_func.args
        kwargs = partial_func.keywords
        command = {}
        command['command'] = func.__name__
        command['command_type'] = type(func)
        command['has_self'] = has_self
        command['args'] = args
        command['kwargs'] = kwargs
        command['arg_types'] = [type(x) for x in args]
        command['kwarg_types'] = [type(kwargs[x]) for x in kwargs]
        return command


    ## Grid-specific method hooking

    def hook_tensor_send(service_self):
        def send_(self, workers):
            workers = tu.check_workers(workers) # makes singleton, if needed
            for worker in workers:
                # TODO: actually generalize this to multiple workers
                # TODO: sync or async? likely won't be worth doing async,
                #       but should check (low priority)
                service_self.send_obj(self, worker)
            self.is_pointer_to_remote = True
            self.owners = workers
            self.zero_()
            return self

        for torch_type in tensor_types:
            setattr(torch_type, 'send_', send_)

    def hook_tensor_get(service_self):
        def get_(self, reduce = lambda x: torch.cat(x).mean(0)):
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

        for torch_type in tensor_types:
            setattr(torch_type, 'get_', get_)

    # TODO: Generalize to other tensor types
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

            del self.objects[v.id]

            if (msg['id'] in self.objects.keys()):
                v_orig = self.objects[msg['id']].set_(v)
                return v_orig
            else:
                self.objects[msg['id']] = v
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
                    result = self.register_object(result, False)
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
                    args, kwargs = self.send_command(command, worker)
                    # TODO: Create local object with same owners and id as
                    #       result of computation on remote;
                    #       helps resolve both #132 and #130
                return args, kwargs # TODO: See Issue #130
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
            if self.is_pointer_to_remote:
                command = service_self.compile_command(part, has_self=True)
                tensorvars = tu.get_tensorvars(service_self, command)
                has_remote, multiple_owners, owners = tu.check_tensorvars(tensorvars)
                if has_remote and not multiple_owners:
                    for worker in owners: # Right now, this can only be singleton
                        print("""Placeholder print for sending command to worker {}""".format(worker))
                        args, kwargs = service_self.send_command(command, worker)
                        # TODO: Create local object with same owners and id as
                        #       result of computation on remote;
                        #       helps resolve both #132 and #130
                else:
                    raise NotImplementedError("""MPC not yet implemented:
                        Torch objects need to be on the same machine in
                        order to compute with them.""")
                return args, kwargs # TODO: See Issue #130
            else:
                result = part.func(self, *args, **kwargs)
                if (type(result) in service_self.tensorvar_types and 
                    not hasattr(result, 'owner')):
                    result = service_self.register_object(result, False)
                return result
        return send_to_workers


    ## Special Tensor method hooks
    def hook_tensor___init__(service_self, tensor_type):
        def new___init__(self, *args):
            super(tensor_type, self).__init__()
            self = service_self.register_object(self, False)

        tensor_type.__init__ = new___init__
    
    def hook_tensor___new__(service_self, tensor_type):
        tensor_type.old___new__ = tensor_type.__new__
        def new___new__(cls, *args, **kwargs):
            result = cls.old___new__(cls, *args,  **kwargs)
            result = service_self.register_object(result, False)
            return result
        
        tensor_type.__new__ = new___new__

    def hook_tensor___repr__(service_self, tensor_type):
        tensor_type.old__repr__ = tensor_type.__repr__
        def new___repr__(self):
            if service_self.worker.id in self.owners:
                return self.old__repr__()
            else:
                return "[ {} - Location:{} ]".format(tensor_type, self.owners)

        tensor_type.__repr__ = new___repr__


    ## Special Variable method hooks
    def hook_var___new__(service_self):
        torch.autograd.variable.Variable.old___new__ = torch.autograd.variable.Variable.__new__
        def new___new__(cls, *args, **kwargs):
            result = cls.old___new__(cls, *args,  **kwargs)
            result = service_self.register_object(result, False)
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
                    self.old_data, False)
                self.data_registered = True
            return self.old_data
        
        @property
        def new_grad(self):
            try:
                self.grad_registered
            except AttributeError:
                if self.old_grad is not None:
                    self.old_grad = service_self.register_object(
                        self.old_grad, False)
                    self.grad_registered = True
            return self.old_grad
        
        torch.autograd.variable.Variable.data = new_data
        torch.autograd.variable.Variable.grad = new_grad


    ## Overloading Torch objects

    # TODO: Issue #132 undo dependency on worker_ids -- no point wasting
    #       time integrating worker_ids into the rest if we're going to
    #       rewrite that part anyway (and we definitely need to rewrite that)

    def hook_torch_module(self, worker_ids):
        print('Overloading Torch module')
        for attr in self.torch_funcs:
            if attr == 'typename':
                continue
            lit = getattr(torch, attr)
            if (type(lit) in [FunctionType, BuiltinFunctionType]):
                passer = self.pass_func_args(lit)
                new_attr = self.overload_function(passer)
                setattr(torch, attr, new_attr)

    def hook_tensor(self, tensor_type, worker_ids):
        print('Overloading {}'.format(tensor_type.__name__))
        self.hook_tensor___init__(tensor_type)
        self.hook_tensor___new__(tensor_type)
        self.hook_tensor___repr__(tensor_type)
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

    def hook_variable(self, worker_ids):
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
