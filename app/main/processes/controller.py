from .federated_learning_process import FLProcess
from .federated_learning_cycle import FederatedLearningCycle

import hashlib
import uuid
from ..codes import MSG_FIELD, CYCLE
from ..exceptions import (
    CycleNotFoundError,
    ProtocolNotFoundError,
    PlanNotFoundError,
    ModelNotFoundError,
    ProcessFoundError,
    FLProcessConflict,
)

from ..controller.processes import Processes
from ..controller.cycles import Cycles
from ..controller.models import Models
from ..controller.workers import Workers

import random
from functools import reduce
from .helpers import unserialize_model_params, serialize_model_params
import torch as th
import json
import logging


class FLController:
    """ This class implements controller design pattern over the federated learning processes. """

    def __init__(self):
        self._processes = Processes()
        self._cycles = Cycles()
        self._models = Models()
        self._workers = Workers()

    def create_process(
        self,
        model,
        client_plans,
        client_config,
        server_config,
        server_averaging_plan,
        client_protocols=None,
    ):
        """ Register a new federated learning process
            Args:
                model: Model object.
                client_plans : an object containing syft plans.
                client_protocols : an object containing syft protocols.
                client_config: the client configurations
                server_averaging_plan: a function that will instruct PyGrid on how to average model diffs that are returned from the workers.
                server_config: the server configurations
            Returns:
                process : FLProcess Instance.
            Raises:
                FLProcessConflict (PyGridError) : If Process Name/Version already exists.
        """
        cycle_len = server_config["cycle_length"]

        # Create a new federated learning process
        # 1 - Create a new process
        # 2 - Save client plans/protocols
        # 3 - Save Server AVG plan
        # 4 - Save Client/Server configs
        _process = self._processes.create(
            client_config,
            client_plans,
            client_protocols,
            server_config,
            server_averaging_plan,
        )

        # Save Model
        # Define the initial version ( first checkpoint)
        _model = self._models.create(model, _process)

        # Create the initial cycle
        _cycle = self._cycles.create(_process.id, _process.version, cycle_len)

        return _process

    def last_cycle(self, worker_id: str, name: str, version: str) -> int:
        """ Retrieve the last time the worker participated from this cycle.
            Args:
                worker_id: Worker's ID.
                name: Federated Learning Process Name.
                version: Model's version.
            Return:
                last_participation: Index of the last cycle assigned to this worker.
        """
        process = self._processes.get(name=name, version=version)
        return self._cycles.last_participation(process, worker_id)

    def assign(self, name: str, version: str, worker, last_participation: int):
        """ Assign a new worker  the specified federated training worker cycle
            Args:
                name: Federated learning process name.
                version: Federated learning process version.
                worker: Worker Object.
                last_participation: The last time that this worker worked on this fl process.
            Return:
                last_participation: Index of the last cycle assigned to this worker.
        """
        _accepted = False

        if version:
            _fl_process = self._processes.first(name=name, version=version)
        else:
            _fl_process = self._processes.last(name=name)

        server_config, client_config = self._processes.get_configs(
            name=name, version=version
        )

        # Retrieve the last cycle used by this fl process/ version
        _cycle = self._cycles.last(_fl_process.id, None)

        # Check if already exists a relation between the worker and the cycle.
        _assigned = self._cycles.is_assigned(worker.id, _cycle.id)

        # Check bandwith
        _comp_bandwith = self._workers.is_eligible(worker.id, server_config)

        # Check if the current worker is allowed to join into this cycle
        _allowed = True

        # TODO wire intelligence
        # (
        #     last_participation + server.config["do_not_reuse_workers_until_cycle"]
        #     >= _cycle.sequence
        # )

        _accepted = (not _assigned) and _comp_bandwith and _allowed
        if _accepted:
            # Assign
            # 1 - Generate new request key
            # 2 - Assign the worker with the cycle.
            key = self._generate_hash_key(uuid.uuid4().hex)
            _worker_cycle = self._cycles.assign(worker, _cycle, key)

            # Create a plan dictionary
            _plans = self._processes.get_plans(
                fl_process_id=_fl_process.id, is_avg_plan=False
            )

            # Create a protocol dictionary
            _protocols = self._processes.get_protocols(fl_process_id=_fl_process.id)

            # Get model ID
            _model = self._models.get(_fl_process.id)
            return {
                CYCLE.STATUS: "accepted",
                CYCLE.KEY: _worker_cycle.request_key,
                CYCLE.VERSION: _cycle.version,
                MSG_FIELD.MODEL: name,
                CYCLE.PLANS: _plans,
                CYCLE.PROTOCOLS: _protocols,
                CYCLE.CLIENT_CONFIG: client_config,
                MSG_FIELD.MODEL_ID: _model.id,
            }
        else:
            n_completed_cycles = self._cycles.count(
                fl_process_id=_fl_process.id, is_completed=True
            )

            _max_cycles = server_config.get["num_cycles"]

            response = {
                CYCLE.STATUS: "rejected",
                MSG_FIELD.MODEL: name,
                CYCLE.VERSION: _cycle.version,
            }

            # If it's not the last cycle, add the remaining time to the next cycle.
            if n_completed_cycles < _max_cycles:
                remaining = _cycle.end - datetime.now()
                response[CYCLE.TIMEOUT] = str(remaining)

            return response

    def _generate_hash_key(self, primary_key: str) -> str:
        """ Generate SHA256 Hash to give access to the cycle.
            Args:
                primary_key : Used to generate hash code.
            Returns:
                hash_code : Hash in string format.
        """
        return hashlib.sha256(primary_key.encode()).hexdigest()

    def add_worker_diff(self, worker_id: str, request_key: str, diff: bin):
        """Store reported diff"""
        worker_cycle = self._worker_cycle.first(
            worker_id=worker_id, request_key=request_key
        )
        if not worker_cycle:
            raise ProcessLookupError

        worker_cycle.is_completed = True
        worker_cycle.completed_at = datetime.utcnow()
        worker_cycle.diff = diff
        self._worker_cycle.update()

        return worker_cycle.cycle_id

    def complete_cycle(self, cycle_id: str):
        """Checks if the cycle is completed and runs plan avg"""
        logging.info("running complete_cycle for cycle_id: %s" % cycle_id)
        cycle = self._cycles.first(id=cycle_id)
        logging.info("found cycle: %s" % str(cycle))

        if cycle.is_completed:
            logging.info("cycle is already completed!")
            return

        _server_config = self._configs.first(
            is_server_config=True, fl_process_id=cycle.fl_process_id
        )
        server_config = _server_config.config
        logging.info("server_config: %s" % json.dumps(server_config, indent=2))
        completed_cycles_num = self._worker_cycle.count(
            cycle_id=cycle_id, is_completed=True
        )
        logging.info("# of diffs: %d" % completed_cycles_num)

        min_worker = server_config.get("min_worker", 3)
        max_worker = server_config.get("max_worker", 3)
        received_diffs_exceeds_min_worker = completed_cycles_num >= min_worker
        received_diffs_exceeds_max_worker = completed_cycles_num >= max_worker
        cycle_ended = True  # check cycle.cycle_time (but we should probably track cycle startime too)

        # Hmm, I don't think there should be such connection between ready_to_average, max_workers, and received_diffs
        # I thought max_workers just caps total number of simultaneous workers
        # 'cycle end' condition should probably depend on cycle_length regardless of number of actual received diffs
        # another 'cycle end' condition can be based on min_diffs
        ready_to_average = (
            True
            if (
                (received_diffs_exceeds_max_worker or cycle_ended)
                and received_diffs_exceeds_min_worker
            )
            else False
        )

        no_protocol = True  # only deal with plans for now

        logging.info("ready_to_average: %d" % int(ready_to_average))

        if ready_to_average and no_protocol:
            self._average_plan_diffs(server_config, cycle)

    def _average_plan_diffs(self, server_config: dict, cycle):
        """ skeleton code
                Plan only
                - get cycle
                - track how many has reported successfully
                - get diffs: list of (worker_id, diff_from_this_worker) on cycle._diffs
                - check if we have enough diffs? vs. max_worker
                - if enough diffs => average every param (by turning tensors into python matrices => reduce th.add => torch.div by number of diffs)
                - save as new model value => M_prime (save params new values)
                - create new cycle & new checkpoint
                at this point new workers can join because a cycle for a model exists
        """
        logging.info("start diffs averaging!")
        logging.info("cycle: %s" % str(cycle))
        logging.info("fl id: %d" % cycle.fl_process_id)
        _model = self.get_model(fl_process_id=cycle.fl_process_id)
        logging.info("model: %s" % str(_model))
        model_id = _model.id
        logging.info("model id: %d" % model_id)
        _checkpoint = self.get_model_checkpoint(model_id=model_id)
        logging.info("current checkpoint: %s" % str(_checkpoint))
        model_params = unserialize_model_params(_checkpoint.values)
        logging.info("model params shapes: %s" % str([p.shape for p in model_params]))

        # Here comes simple hardcoded avg plan
        # it won't be always possible to retrieve and unserialize all diffs due to memory constrains
        # needs some kind of iterative or streaming approach,
        # e.g.
        # for diff_N in diffs:
        #    avg = avg_plan(avg, N, diff_N)
        # and the plan is:
        # avg_next = (avg_current*(N-1) + diff_N) / N
        reports_to_average = self._worker_cycle.query(
            cycle_id=cycle.id, is_completed=True
        )
        diffs = [unserialize_model_params(report.diff) for report in reports_to_average]

        # Again, not sure max_workers == number of diffs to avg
        diffs = random.sample(diffs, server_config.get("max_workers"))

        raw_diffs = [
            [diff[model_param] for diff in diffs]
            for model_param in range(len(model_params))
        ]
        logging.info("raw diffs lengths: %s" % str([len(row) for row in raw_diffs]))

        sums = [reduce(th.add, param) for param in raw_diffs]
        logging.info("sums shapes: %s" % str([sum.shape for sum in sums]))

        diff_avg = [th.div(param, len(diffs)) for param in sums]
        logging.info("diff_avg shapes: %s" % str([d.shape for d in diff_avg]))

        # apply avg diff!
        _updated_model_params = [
            model_param - diff_param
            for model_param, diff_param in zip(model_params, diff_avg)
        ]
        logging.info(
            "_updated_model_params shapes: %s"
            % str([p.shape for p in _updated_model_params])
        )

        # make new checkpoint
        serialized_params = serialize_model_params(_updated_model_params)
        _new_checkpoint = self.create_checkpoint(model_id, serialized_params)
        logging.info("new checkpoint: %s" % str(_new_checkpoint))

        # mark current cycle completed
        cycle.is_completed = True
        self._cycles.update()

        completed_cycles_num = self._cycles.count(
            fl_process_id=cycle.fl_process_id, is_completed=True
        )
        logging.info("completed_cycles_num: %d" % completed_cycles_num)
        max_cycles = server_config.get("num_cycles")
        if completed_cycles_num < max_cycles:
            # make new cycle
            _new_cycle = self.create_cycle(cycle.fl_process_id, cycle.version)
            logging.info("new cycle: %s" % str(_new_cycle))
        else:
            logging.info("FL is done!")
