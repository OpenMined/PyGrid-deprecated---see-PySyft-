from filelock import Timeout, FileLock
from grid import ipfsapi
import keras
import os
import json
from colorama import Fore, Back, Style
import sys


def get_ipfs_api(ipfs_addr='127.0.0.1', port=5001):
    try:
        return ipfsapi.connect(ipfs_addr, port)
    except:
        print(f'\n{Fore.RED}ERROR: {Style.RESET_ALL}could not connect to IPFS.  Is your daemon running with pubsub support at {ipfs_addr} on port {port}')
        sys.exit()

def serialize_torch_model(self, model, **kwargs):
    """
    kwargs are the arguments needed to instantiate the model
    """
    state = {'state_dict': model.state_dict(), 'kwargs': kwargs}
    torch.save(state, 'temp_model.pth.tar')
    with open('temp_model.pth.tar', 'rb') as f:
        model_bin = f.read()
    return model_bin

def deserialize_torch_model(self, model_bin, model_class, **kwargs):
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


def keras2ipfs(model):
    return get_ipfs_api().add_bytes(serialize_keras_model(model))

def torch2ipfs(model):
    return get_ipfs_api().add_bytes(serialize_torch_model(model))

def ipfs2torch(model):
    model_bin = get_ipfs_api().cat(model_addr)
    return deserialize_torch_model(model_bin)

def ipfs2keras(model_addr):
    model_bin = get_ipfs_api().cat(model_addr)
    return deserialize_keras_model(model_bin)

def serialize_keras_model(model):
    lock = FileLock('temp_model.h5.lock')
    with lock:
        model.save('temp_model.h5')
        with open('temp_model.h5', 'rb') as f:
            model_bin = f.read()
            f.close()
        return model_bin


def deserialize_keras_model(model_bin):
    lock = FileLock('temp_model2.h5.lock')
    with lock:
        with open('temp_model2.h5', 'wb') as g:
            g.write(model_bin)
            g.close()
        model = keras.models.load_model('temp_model2.h5')
        return model

# def load_tasks():

def save_best_model_for_task(task, model):
    if not os.path.exists(".openmined"):
        os.makedirs(".openmined")

    if not os.path.exists(".openmined/models.json"):
        with open(".openmined/models.json", "w") as model_file:
            json.dump({}, model_file)

    models = {}
    with open(".openmined/models.json", "r") as model_file:
        models = json.loads(model_file.read())

    models[task] = keras2ipfs(model)

    with open(".openmined/models.json", "w") as model_file:
        json.dump(models, model_file)


def best_model_for_task(task, return_model=False):
    if not os.path.exists('.openmined/models.json'):
        return None

    with open('.openmined/models.json', 'r') as model_file:
        models = json.loads(model_file.read())
        if task in models.keys():
            if return_model:
                return ipfs2keras(models[task])
            else:
                return models[task]

    return None

def load_task(name):
    if not os.path.exists('.openmined/tasks.json'):
        return None

    with open('.openmined/tasks.json', 'r') as task_file:
        tasks = json.loads(task_file.read())

    for task in tasks:
        if task['name'] == name:
            return task

def store_task(name, address):
    # config file with openmined data dir
    if not os.path.exists(".openmined"):
        os.makedirs(".openmined")

    if not os.path.exists(".openmined/tasks.json"):
        with open(".openmined/tasks.json", "w") as task_file:
            json.dump([], task_file)

    with open(".openmined/tasks.json", "r") as task_file:
        tasks = json.loads(task_file.read())

    task = {
        'name': name,
        'address': address
    }

    if task not in tasks:
        print("storing task", task['name'])
        tasks.append(task)

        with open(".openmined/tasks.json", "w") as task_file:
            json.dump(tasks, task_file)
