import os
import json

from pathlib import Path

from . import utils
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
    tensorvar_args = [args[i] for i in range(len(args)) if arg_types[i] in self.tensorvar_types]
    tensorvar_kwvals = [kwargs[i][1] for i in range(len(kwargs)) if kwarg_types[i] in self.tensorvar_types]
    return tensorvar_args + tensorvar_kwvals
    
def check_tensorvars(tensorvars):
    # Had an efficiency reason for these TODOs, but forgot...

    # TODO: turn this line into a function `check_remote`
    has_remote = any([tensorvar.is_pointer for tensorvar in tensorvars])
    # TODO: turn the following into a function `get_owners`
    print([tensorvar.owners for tensorvar in tensorvars])
    owners = list(set([owner
        for tensorvar in tensorvars
        for owner in tensorvar.owners]))
    multiple_owners = len(owners) != 1
    return has_remote, multiple_owners, owners

def replace_tensorvar(x):
    try:
        if torch.old_is_tensor(x) or isinstance(x, torch.autograd.Variable):
            return '_fl.{}'.format(x.id)
        else:
            [replace_tensorvar(i) for i in x]
    except (AttributeError, TypeError):
        return x

def replace_in_command(command_msg):
    command_msg['args'] = tu.map_tuple(
        None, command_msg['args'], tu.replace_tensorvar)
    command_msg['kwargs'] = tu.map_dict(
        None, command_msg['kwargs'], tu.replace_tensorvar)
    try:
        command_msg['self'] = tu.replace_tensorvar(command_msg['self'])
    except KeyError:
        pass
    return command_msg

# Client needs to identify a tensor before sending commands that use it
def id_tensorvar(x):
    pat = re.compile('_fl.(.*)')
    try:
        if isinstance(x, str):
            return pat.search(x).group(1)
        else:
            return [id_tensorvar(i) for i in x]
    except AttributeError:
        return x

# Safety checks for serializing and deserializing torch objects
# Desperately needs stress testing before going out in the wild
map_torch_type = {
    'torch.FloatTensor':torch.FloatTensor,
    'torch.DoubleTensor':torch.DoubleTensor,
    'torch.HalfTensor':torch.HalfTensor,
    'torch.ByteTensor':torch.ByteTensor,
    'torch.CharTensor':torch.CharTensor,
    'torch.ShortTensor':torch.ShortTensor,
    'torch.IntTensor':torch.IntTensor,
    'torch.LongTensor':torch.LongTensor,
    'torch.autograd.variable.Variable':torch.autograd.variable.Variable,
    'torch.nn.parameter.Parameter':torch.nn.parameter.Parameter
}

def types_guard(obj_type):
    return map_torch_type[obj_type]

def tensor_contents_guard(contents):
    # TODO: check to make sure the incoming list isn't dangerous to use for
    #       constructing a tensor (likely non-trivial)
    pass

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
        return {key:func(service, val) for key, val in kwargs.items()}
    else:
        return {key:func(val) for key, val in kwargs.items()}


# Serializing and deserializing torch objects
def hook_tensor_serde(service_self, tensor_type):
    def ser(self, include_data=True):
        tensor_msg = {}
        tensor_msg['torch_type'] = self.type()
        if (include_data):
            tensor_msg['data'] = self.tolist()
        tensor_msg['id'] = self.id
        tensor_msg['owners'] = self.owners
        return json.dumps(msg)

    def de(self, tensor_msg):
        if (type(tensor_msg) == str):
            tensor_msg = json.loads(tensor_msg)
        _tensor_type = tensor_msg['type']
        try:
            tensor_type = types_guard(_tensor_type)
        except KeyError:
            RuntimeError('Object type {} is not supported'.format(_tensor_type))
        # this could be a significant failure point, security-wise
        if ('data' in msg.keys()):
            data = msg['data']
            tensor_contents_guard(data)
            v = tensor_type(msg['data'])
        else:
            v = torch.old_zeros(0).type(tensor_type)

        # TODO: check everything below here

        del service_self.worker.objects[v.id]

        if (msg['id'] in service_self.worker.objects.keys()):
            v_orig = service_self.worker.objects[msg['id']].set_(v)
            return v_orig
        else:
            self.worker.objects[msg['id']] = v
            v.id = msg['id']
            v.owner = msg['owner']
            return v

    tensor_type.ser = ser
    tensor_type.de = de

def hook_var_serde(service_self):
    # TODO
    pass

# Serializing torch stuffs (probably deprecated at this point)
def torch2ipfs(model):
    pass


def ipfs2torch(model_addr):
    pass


def serialize_torch_model(model, **kwargs):
    """
    kwargs are the arguments needed to instantiate the model
    """
    state = {'state_dict': model.state_dict(), 'kwargs': kwargs}
    torch.save(state, 'temp_model.pth.tar')
    with open('temp_model.pth.tar', 'rb') as f:
        model_bin = f.read()
    return model_bin


def deserialize_torch_model(model_bin, model_class, **kwargs):
    """
    model_class is needed since PyTorch uses pickle for serialization
        see https://discuss.pytorch.org/t/loading-pytorch-model-without-a-code/12469/2 for details
    kwargs are the arguments needed to instantiate the model from model_class
    """
    with open('temp_model2.pth.tar', 'wb') as g:
        g.write(model_bin)
    state = torch.load()
    model = model_class(**state['kwargs'])
    model.load_state_dict(state['state_dict'])
    return model


def save_best_torch_model_for_task(task, model):
    utils.ensure_exists(f'{Path.home()}/.openmined/models.json', {})
    with open(f"{Path.home()}/.openmined/models.json", "r") as model_file:
        models = json.loads(model_file.read())

    models[task] = torch2ipfs(model)

    with open(f"{Path.home()}/.openmined/models.json", "w") as model_file:
        json.dump(models, model_file)


def best_torch_model_for_task(task, return_model=False):
    if not os.path.exists(f'{Path.home()}/.openmined/models.json'):
        return None

    with open(f'{Path.home()}/.openmined/models.json', 'r') as model_file:
        models = json.loads(model_file.read())
        if task in models.keys():
            if return_model:
                return ipfs2torch(models[task])
            else:
                return models[task]

    return None
