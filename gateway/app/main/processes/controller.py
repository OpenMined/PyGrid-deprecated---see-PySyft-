from .federated_learning_process import FLProcess
from .federated_learning_cycle import FederatedLearningCycle
from ..storage import models
from ..storage.warehouse import Warehouse
from sqlalchemy import func
from random import randint

BIG_INT = 2 ** 32


class FLController:
    """ This class implements controller design pattern over the federated learning processes. """

    def __init__(self):
        self._processes = Warehouse(models.FLProcess)
        self._cycles = Warehouse(models.Cycle)
        self._worker_cycle = Warehouse(models.WorkerCycle)
        self._configs = Warehouse(models.Config)
        self._plans = Warehouse(models.Plan)
        self._protocols = Warehouse(models.Protocol)
        self._models = Warehouse(models.Model)

    def create_cycle(self, model_id: str, version: str, cycle_time: int = 2500):
        """ Create a new federated learning cycle.
            Args:
                model_id: Model's ID.
                worker_id: Worker's ID.
                cycle_time: Remaining time to finish this cycle.
            Returns:
                fd_cycle: Cycle Instance.
        """
        _fl_process = self._processes.query(model=model_id)

        if _fl_process:
            # Retrieve a list of cycles using the same model_id/version
            sequence_number = len(
                self._cycles.query(fl_process_id=_fl_process.id, version=version)
            )

            self._cycles.register(
                id=randint(0, BIG_INT),
                start=datetime,
                end=datetime,
                sequence=sequence_number + 1,
                version=version,
                fl_process_id=_fl_process,
            )

    def get_cycle(self, model_id: str, version: str):
        """ Retrieve a registered cycle.
            Args:
                model_id: Model's ID.
                version: Model's version.
            Returns:
                cycle: Cycle Instance / None
        """
        _model = self._models.query(id=model_id)
        _cycle = self._cycles.query(fl_process_id=_model.fl_process_id, version=version)

        if _cycle:
            return cycle.last()

    def delete_cycle(self, *kwargs):
        """ Delete a registered Cycle.
            Args:
                model_id: Model's ID.
        """
        self._cycles.delete(kwargs)

    def last_participation(self, worker_id: str, model_id: str, version: str) -> int:
        """ Retrieve the last time the worker participated from this cycle.
            Args:
                worker_id: Worker's ID.
                model_id: Model's ID.
                version: Model's version.
            Return:
                last_participation: Index of the last cycle assigned to this worker.
        """
        _model = self._models.query(id=model_id)
        _cycles = self._cycles.query(fl_process_id=_model.fl_process_id)

        last = 0
        if not _cycles:
            return last

        for cycle in _cycles:
            worker_cycle = self._worker_cycle.query(
                cycle_id=cycle.id, worker_id=worker_id
            )
            if worker_cycle and cycle.sequence > last:
                last = cycle.sequence

        return last

    def create_process(
        self,
        model_id,
        client_plans,
        client_config,
        server_config,
        server_averaging_plan,
        client_protocols=None,
    ):
        """ Register a new federated learning process
            Args:
                model_id: Model's ID.
                client_plans : an object containing syft plans.
                client_protocols : an object containing syft protocols.
                client_config: the client configurations
                server_averaging_plan: a function that will instruct PyGrid on how to average model diffs that are returned from the workers.
                server_config: the server configurations
            Returns:
                process : FLProcess Instance.
        """

        # Register a new FL Process
        fl_process = self._processes.register(id=randint(0, BIG_INT))

        _model = self._models.query(id=model_id)
        if not _model:
            self._models.register(id=model_id, flprocess=fl_process)
        print(_model)

        # Register new Plans into the database
        for key, value in client_plans.items():
            self._plans.register(
                id=randint(0, BIG_INT), name=key, value=value, plan_flprocess=fl_process
            )

        # Register new Protocols into the database
        for key, value in client_protocols.items():
            self._protocols.register(
                id=randint(0, BIG_INT),
                name=key,
                value=value,
                protocol_flprocess=fl_process,
            )

        # Register the average plan into the database
        self._plans.register(
            id=randint(0, BIG_INT), value=value, avg_flprocess=fl_process
        )

        # Register the client/server setup configs
        client_config = self._configs.register(
            id=randint(0, BIG_INT),
            config=client_config,
            server_flprocess_config=fl_process,
        )
        server_config = self._configs.register(
            id=randint(0, BIG_INT),
            config=server_config,
            client_flprocess_config=fl_process,
        )

        return fl_process

    def delete_process(self, **kwargs):
        """ Remove a registered federated learning process.
            Args:
                pid : Id used identify the desired process. 
        """
        self._processes.delete(**kwargs)

    def get_process(self, **kwargs):
        """ Retrieve the desired federated learning process.
            Args:
                pid : Id used to identify the desired process.
            Returns:
                process : FLProcess Instance or None if it wasn't found.
        """
        return self._processes.query(**kwargs)
