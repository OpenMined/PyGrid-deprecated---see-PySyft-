from datetime import datetime, timedelta
from ..models.warehouse import Warehouse
from ..models.cycle import Cycle
from ..models.worker_cycle import WorkerCycle
from ..exceptions import CycleNotFoundError


class Cycles:
    def __init__(self):
        self._cycles = Warehouse(Cycle)
        self._worker_cycles = Warehouse(WorkerCycle)

    def create(self, fl_process_id: str, version: str, cycle_time: int = 2500):
        """ Create a new federated learning cycle.
            Args:
                fl_process_id: FL Process's ID.
                version: Version (?)
                cycle_time: Remaining time to finish this cycle.
            Returns:
                fd_cycle: Cycle Instance.
        """
        _new_cycle = None

        # Retrieve a list of cycles using the same model_id/version
        sequence_number = len(
            self._cycles.query(fl_process_id=fl_process_id, version=version)
        )
        _now = datetime.now()
        _end = _now + timedelta(seconds=cycle_time)
        _new_cycle = self._cycles.register(
            start=_now,
            end=_end,
            sequence=sequence_number + 1,
            version=version,
            fl_process_id=fl_process_id,
        )

        return _new_cycle

    def last_participation(self, process: int, worker_id: str):
        """ Retrieve the last time the worker participated from this cycle.
            Args:
                process_id : Federated Learning Process ID.
                worker_id: Worker's ID.
            Returns:
                last_participation: last cycle.
        """
        _cycles = self._cycles.get(fl_process_id=process.id)

        last = 0
        if not len(_cycles):
            return last

        for cycle in _cycles:
            worker_cycle = self._worker_cycles.first(
                cycle_id=cycle.id, worker_id=worker_id
            )
            if worker_cycle and cycle.sequence > last:
                last = cycle.sequence

        return last

    def last(self, fl_process_id: int, version: str = None):
        """ Retrieve the last not completed registered cycle.
            Args:
                model_id: Model's ID.
                version: Model's version.
            Returns:
                cycle: Cycle Instance / None
        """
        if version:
            _cycle = self._cycles.last(
                fl_process_id=fl_process_id, version=version, is_completed=False
            )
        else:
            _cycle = self._cycles.last(fl_process_id=fl_process_id, is_completed=False)

        if not _cycle:
            raise CycleNotFoundError

        return _cycle

    def delete(self, **kwargs):
        """ Delete a registered Cycle.
            Args:
                model_id: Model's ID.
        """
        self._cycles.delete(**kwargs)

    def is_assigned(self, worker_id: str, cycle_id: str):
        """ Check if a workers is already assigned to an specific cycle.
            Args:
                worker_id : Worker's ID.
                cycle_id : Cycle's ID.
            Returns:
                result : Boolean Flag.
        """
        return self._worker_cycle.first(worker_id=worker.id, cycle_id=_cycle.id) != None

    def assign(self, worker, cycle, hash_key: str):
        _worker_cycle = self._worker_cycles.register(
            worker=worker, cycle=cycle, request_key=hash_key,
        )

        return _worker_cycle

    def validate(self, worker_id: str, cycle_id: str, request_key: str):
        """ Validate Worker's request key.
            Args:
                worker_id: Worker's ID.
                cycle_id: Cycle's ID.
                request_key: Worker's request key.
            Returns:
                result: Boolean flag
            Raises:
                CycleNotFoundError (PyGridError) : If not found any relation between the worker and cycle.
        """
        _worker_cycle = self._worker_cycles.first(
            worker_id=worker_id, cycle_id=cycle_id
        )

        if not _worker_cycle:
            raise CycleNotFoundError

        return _worker_cycle.request_key == request_key

    def count(self, **kwargs):
        return self._cycles.count(**kwargs)