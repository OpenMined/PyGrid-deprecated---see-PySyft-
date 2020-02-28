from .federated_learning_process import FLProcess
from .federated_learning_cycle import FederatedLearningCycle
from ..storage import models
from ..storage.warehouse import Warehouse
from sqlalchemy import func
from datetime import datetime, timedelta
import hashlib
import uuid
from ..codes import MSG_FIELD, CYCLE


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

        _new_cycle = None
        if _fl_process:
            # Retrieve a list of cycles using the same model_id/version
            sequence_number = len(
                self._cycles.query(fl_process_id=_fl_process.id, version=version)
            )

            _new_cycle = self._cycles.register(
                start=datetime.now(),
                end=datetime.now(),
                sequence=sequence_number + 1,
                version=version,
                fl_process_id=_fl_process,
            )

        return _new_cycle

    def get_cycle(self, model_id: str, version: str):
        """ Retrieve a registered cycle.
            Args:
                model_id: Model's ID.
                version: Model's version.
            Returns:
                cycle: Cycle Instance / None
        """
        _model = self._models.first(id=model_id)
        if version:
            _cycle = self._cycles.last(
                fl_process_id=_model.fl_process_id, version=version
            )
        else:
            _cycle = self._cycles.last(fl_process_id=_model.fl_process_id)

        if _cycle:
            return _cycle

    def delete_cycle(self, **kwargs):
        """ Delete a registered Cycle.
            Args:
                model_id: Model's ID.
        """
        self._cycles.delete(**kwargs)

    def last_participation(self, worker_id: str, model_id: str, version: str) -> int:
        """ Retrieve the last time the worker participated from this cycle.
            Args:
                worker_id: Worker's ID.
                model_id: Model's ID.
                version: Model's version.
            Return:
                last_participation: Index of the last cycle assigned to this worker.
        """
        _model = self._models.first(id=model_id)
        _cycles = self._cycles.query(fl_process_id=_model.fl_process_id)

        last = 0
        if not len(_cycles):
            return last

        for cycle in _cycles:
            worker_cycle = self._worker_cycle.first(
                cycle_id=cycle.id, worker_id=worker_id
            )
            if worker_cycle and cycle.sequence > last:
                last = cycle.sequence

        return last

    def assign(self, model_id: str, version: str, worker, last_participation: int):
        _accepted = False

        # Retrieve model to track federated learning process
        _model = self._models.first(id=model_id)

        # Retrieve server configs
        server = self._configs.first(
            fl_process_id=_model.fl_process_id, client_config=True
        )

        # Retrieve the last cycle used by this fl process/ version
        if version:
            _cycle = self._cycles.last(
                fl_process_id=_model.fl_process_id, version=version
            )
        else:
            _cycle = self._cycles.last(fl_process_id=_model.fl_process_id)

        # Retrieve an WorkerCycle instance if this worker is already registered on this cycle.
        _worker_cycle = self._worker_cycle.query(
            worker_id=worker.id, cycle_id=_cycle.id
        )

        # Check bandwith
        _comp_bandwith = (
            worker.avg_upload > server.config["minimum_upload_speed"]
        ) and (worker.avg_download > server.config["minimum_download_speed"])

        # Check if the current worker is allowed to join into this cycle
        _allowed = (
            last_participation + server.config["do_not_reuse_workers_until_cycle"]
            >= _cycle.sequence
        )

        _accepted = (not _worker_cycle) and _comp_bandwith and _allowed
        if _accepted:
            _worker_cycle = self._worker_cycle.register(
                worker=worker,
                cycle=_cycle,
                request_key=self._generate_hash_key(uuid.uuid4().hex),
            )
            # Create a plan dictionary
            _plans = {
                plan.name: plan.id
                for plan in self._plans.query(
                    fl_process_id=_model.fl_process_id, is_avg_plan=False
                )
            }
            # Create a protocol dictionary
            _protocols = {
                protocol.name: protocol.id
                for protocol in self._protocols.query(
                    fl_process_id=_model.fl_process_id
                )
            }

            return {
                CYCLE.STATUS: "accepted",
                CYCLE.KEY: _worker_cycle.request_key,
                MSG_FIELD.MODEL: str(_model),
                CYCLE.PLANS: _plans,
                CYCLE.PROTOCOLS: _protocols,
                CYCLE.CLIENT_CONFIG: self._configs.first(
                    fl_process_id=_model.fl_process_id, client_config=False
                ).config,
                MSG_FIELD.MODEL_ID: _model.id,
            }
        else:
            if _cycle:
                remaining = _cycle.end - datetime.now()
                return {
                    CYCLE.STATUS: "rejected",
                    CYCLE.TIMEOUT: str(remaining),
                }

    def _generate_hash_key(self, primary_key: str) -> str:
        """ Generate SHA256 Hash to give access to the cycle.
            Args:
                primary_key : Used to generate hash code.
            Returns:
                hash_code : Hash in string format.
        """
        print("Primary key: ", primary_key)
        return hashlib.sha256(primary_key.encode()).hexdigest()

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
        fl_process = self._processes.register()

        _model = self._models.query(id=model_id)
        if not _model:
            self._models.register(id=model_id, flprocess=fl_process)

        # Register new Plans into the database
        for key, value in client_plans.items():
            self._plans.register(name=key, value=value, plan_flprocess=fl_process)

        # Register new Protocols into the database
        for key, value in client_protocols.items():
            self._protocols.register(
                name=key, value=value, protocol_flprocess=fl_process,
            )

        # Register the average plan into the database
        self._plans.register(value=value, avg_flprocess=fl_process, is_avg_plan=True)

        # Register the client/server setup configs
        self._configs.register(
            config=client_config,
            client_config=False,
            server_flprocess_config=fl_process,
        )

        self._configs.register(
            config=server_config, client_config=True, client_flprocess_config=fl_process
        )

        # Create a new cycle
        _now = datetime.now()
        _end = _now + timedelta(seconds=server_config["cycle_length"])
        self._cycles.register(
            start=_now,
            end=_end,
            sequence=0,
            version="1.0.0",
            cycle_flprocess=fl_process,
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
