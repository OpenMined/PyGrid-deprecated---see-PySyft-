# Channels

# Main channel that high level commands are broadcasted on
list_tasks = 'openmined:list_tasks'
add_task = 'openmined:add_task'


def list_tasks_callback(id):
    return f'openmined:list_tasks:{id}'
