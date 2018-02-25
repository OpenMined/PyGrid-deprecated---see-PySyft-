from .. import base

class GridWorker(base.PubSub):

    def __init__(self):
        super().__init__('worker')
