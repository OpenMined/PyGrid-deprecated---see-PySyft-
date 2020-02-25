from .worker import Worker
from ..storage.db_manager import Warehouse
from ..storage import models


class WorkerController:
    """ This class implements controller design pattern over the workers."""

    def __init__(self):
        self.cache = {}
        self._storage = Warehouse(models.Worker)

    def create_worker(self, worker_id: str):
        """ Register a new worker
            Args:
                worker_id: id used to identify the new worker.
            Returns:
                worker: a Worker instance.
        """
        if self._storage.contains(worker_id):
            return self._storage.query(id=worker_id)

        self._storage.register({"id": worker_id})
        worker = Worker(worker_id)
        self.cache[worker.worker_id] = worker
        return self.cache[worker.worker_id]

    def delete_worker(self, worker_id):
        """ Remove a registered worker.
            Args:
                worker_id: Id used identify the desired worker. 
        """
        self._storage.delete(id=worker_id)
        del self.cache[worker_id]

    def get_worker(self, worker_id):
        """ Retrieve the desired worker.
            Args:
                worker_id: Id used to identify the desired worker.
            Returns:
                worker: worker Instance or None if it wasn't found.
        """
        _worker = self.cache.get(worker_id, None)

        if not _worker:
            _worker = self._storage.query(id=worker_id)

        return _worker
