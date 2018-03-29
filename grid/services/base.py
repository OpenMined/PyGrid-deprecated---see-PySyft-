import random
import torch

class BaseService(object):

    def __init__(self, worker):
        self.worker = worker
        self.api = self.worker.api

        ## Torch-specific
        self.tensor_types = [torch.FloatTensor,
                torch.DoubleTensor,
                torch.HalfTensor,
                torch.ByteTensor,
                torch.CharTensor,
                torch.ShortTensor,
                torch.IntTensor,
                torch.LongTensor]
        # torch.nn.Parameter is also technically a var_type,
        # but it inherits all of Variable's hooked methods
        self.var_types = [torch.autograd.variable.Variable]
        self.tensorvar_types = self.tensor_types + self.var_types
        self.tensorvar_types_strs = [x.__name__ for x in self.tensorvar_types]

        # Any commands that don't appear in the following two lists
        # will not execute
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


    def register_object(self, obj, **kwargs):
        # Defaults:
        #   id -- random integer between 0 and 1e10
        #   owners -- list containing local worker's IPFS id
        #   is_pointer -- False

        # TODO: Assign default id more intelligently (low priority)
        #       Consider popping id from long list of unique integers
        keys = kwargs.keys()
        print(keys)
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
        mal_points_here = False
        #mal_points_here = not obj.is_pointer and self.worker.id not in obj.owners
        if mal_points_away or mal_points_here:
            raise RuntimeError(
                'Invalid registry: is_pointer is {} but owners is {}'.format(
                    obj.is_pointer, obj.owners))
        self.worker.objects[obj.id] = obj
        return obj
