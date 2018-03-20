import os
import json

from pathlib import Path

from . import utils

# Helpers for HookService and TorchService
def check_workers(workers):
    if type(workers) is str:
        workers = [workers]
    elif not hasattr(workers, '__iter__'):
        raise TypeError(
            """'workers' must be a string worker ID or an iterable of
            string worker IDs, not {}""".format(type(owners))
            )
    return workers

def get_tensorvars(command):
    args = command['args']
    kwargs = command['kwargs']
    arg_types = command['arg_types']
    kwarg_types = command['kwarg_types']
    tensorvar_args = [args[i] for i in range(len(args)) if arg_types[i] in tensorvar_types]
    tensorvar_kwvals = [kwargs[i][1] for i in range(len(kwargs)) if kwarg_types[i] in tensorvar_types]
    return tensorvar_args + tensorvar_kwvals
    
def check_tensorvars(tensorvars):
    has_remote = any([tensorvar.is_pointer_to_remote for tensorvar in tensorvars])
    multiple_owners = len(set([tensorvar.owner for tensorvar in tensorvars])) != 1
    return has_remote, multiple_owners

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
