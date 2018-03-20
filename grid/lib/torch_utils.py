import os
import json

from pathlib import Path

from . import utils

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
    owners = list(set([owner for tensorvar in tensorvars for owner in tensorvar.owners]))
    multiple_owners = len(owners) != 1
    return has_remote, multiple_owners, owners

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
