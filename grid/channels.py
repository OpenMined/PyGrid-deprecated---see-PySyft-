# Channels

# Main channel that high level commands are broadcasted on
openmined = 'openmined'

list_tasks = 'openmined:list_tasks'
add_task = 'openmined:add_task'
list_models = 'openmined:list_models'
list_workers = 'openmined:list_workers'

def list_tasks_callback(id):
    return f'openmined:list_tasks:{id}'

def list_workers_callback(id):
    return f'openmined:list_workers:{id}'

def add_model(name):
    return f'openmined:task:add:{name}'


# Torch Channels

torch_listen_for_objects = 'openmined:torch_listen_for_objects'

def torch_receive_obj_callback(id):
    return f'openmined:torch_listen_for_objects:{id}'



