import random

class BaseService(object):
    def __init__(self, worker):
        self.worker = worker
        self.api = self.worker.api
        self.objects = {}

    def register_object(self, obj, **kwargs):
        # TODO: Assign default id more intelligently (low priority)
        #       Consider popping id from long list of unique integers
        keys = kwargs.keys()
        obj.id = (kwargs['id']
            if 'id' in keys
            else random.randint(0, 1e10))
        obj.owners = (kwargs['owners']
            if 'owners' in keys
            else [self.worker.id])
        obj.is_pointer = (kwargs['is_pointer']
            if 'is_pointer' in keys
            else False)
        mal_points_away = obj.is_pointer and self.worker.id in obj.owners
        mal_points_here = not obj.is_pointer and self.worker.id not in obj.owners
        if mal_points_away or mal_points_here:
            raise RuntimeError(
                'Invalid registry: is_pointer is {} but owners is {}'.format(
                    obj.is_pointer, obj.owners))
        self.objects[obj.id] = obj
        return obj