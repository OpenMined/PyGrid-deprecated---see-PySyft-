import uuid
import json


from .socket_handler import SocketHandler
from ..codes import MSG_FIELD, RESPONSE_MSG, CYCLE
from ..processes import processes
from ..auth import workers

# Singleton socket handler
handler = SocketHandler()


def host_federated_training(message: dict, socket) -> str:
    """This will allow for training cycles to begin on end-user devices.
        Args:
            message : Message body sended by some client.
            socket: Socket descriptor.
        Returns:
            response : String response to the client
    """
    data = message[MSG_FIELD.DATA]
    response = {}

    try:
        # Retrieve JSON values
        serialized_model = data.get(MSG_FIELD.MODEL, None)  # Only one
        serialized_client_plans = data.get(CYCLE.PLANS, None)  # 1 or *
        serialized_client_protocols = data.get(CYCLE.PROTOCOLS, None)  # 0 or *
        serialized_avg_plan = data.get(CYCLE.AVG_PLAN, None)  # Only one
        client_config = data.get(CYCLE.CLIENT_CONFIG, None)  # Only one
        server_config = data.get(CYCLE.SERVER_CONFIG, None)  # Only one

        # Create a new FL Process
        processes.create_process(
            model=serialized_model,
            client_plans=serialized_client_plans,
            client_protocols=serialized_client_protocols,
            server_averaging_plan=serialized_avg_plan,
            client_config=client_config,
            server_config=server_config,
        )

    except Exception as e:  # Retrieve exception messages such as missing JSON fields.
        response[RESPONSE_MSG.ERROR] = str(e)

    return json.dumps(response)


def authenticate(message: dict, socket) -> str:
    """ New workers should receive a unique worker ID after authenticate on PyGrid platform.
        Args:
            message : Message body sended by some client.
            socket: Socket descriptor.
        Returns:
            response : String response to the client
    """
    response = {}

    # Create a new worker instance and bind it with the socket connection.
    try:
        # Create new worker id
        worker_id = str(uuid.uuid4())

        # Create a link between worker id and socket descriptor
        handler.new_connection(worker_id, socket)

        # Create worker instance
        workers.create_worker(worker_id)

        response[MSG_FIELD.WORKER_ID] = worker_id

    except Exception as e:  # Retrieve exception messages such as missing JSON fields.
        response[RESPONSE_MSG.ERROR] = str(e)

    return json.dumps(response)


def cycle_request(message: dict, socket) -> str:
    """This event is where the worker is attempting to join an active federated learning cycle.
        Args:
            message : Message body sended by some client.
            socket: Socket descriptor.
        Returns:
            response : String response to the client
    """
    data = message[MSG_FIELD.DATA]
    response = {}

    try:
        # Retrieve JSON values
        worker_id = data.get(MSG_FIELD.WORKER_ID, None)
        model_id = data.get(MSG_FIELD.MODEL, None)
        version = data.get(CYCLE.VERSION, None)
        ping = data.get(CYCLE.PING, None)
        download = data.get(CYCLE.DOWNLOAD, None)
        upload = data.get(CYCLE.UPLOAD, None)

        # Retrieve the worker
        worker = workers.get_worker(worker_id)

        # The last time this worker was assigned for this model/version.
        last_participation = processes.last_participation(worker_id, model_id, version)

        # Retrieve the last cycle created for this model_id/version
        cycle = processes.get_cycle(model_id, version)

        _accepted = False

        if worker and cycle:
            _accepted = cycle.assign(worker_id, upload, download, last_participation)

        ### MOCKUP ###

        # Build response
        if _accepted:
            worker.register_cycle(cycle.hash, cycle)
            response[CYCLE.STATUS] = "accepted"
            response[MSG_FIELD.MODEL] = cycle.fl_process.model
            response[CYCLE.VERSION] = version
            response[CYCLE.KEY] = cycle.hash
            response[CYCLE.PLANS] = cycle.fl_process.client_plans
            response[CYCLE.PROTOCOLS] = cycle.fl_process.client_protocols
            response[CYCLE.CLIENT_CONFIG] = cycle.fl_process.client_config
            response[MSG_FIELD.MODEL_ID] = model_id
        else:
            # If worker_id already exists in the current cycle, return False.
            response[CYCLE.STATUS] = "rejected"
            response[CYCLE.TIMEOUT] = cycle.remaining_time + 1

    except Exception as e:  # Retrieve exception messages such as missing JSON fields.
        response[RESPONSE_MSG.ERROR] = str(e)

    return json.dumps(response)


def report(message: dict, socket) -> str:
    """ This method will allow a worker that has been accepted into a cycle
        and finished training a model on their device to upload the resulting model diff.
        Args:
            message : Message body sended by some client.
            socket: Socket descriptor.
        Returns:
            response : String response to the client
    """
    data = message[MSG_FIELD.DATA]
    response = {}

    try:
        model_id = data.get(MSG_FIELD.MODEL, None)
        request_key = data.get(CYCLE.KEY, None)
        diff = data.get(CYCLE.DIFF, None)

        # TODO:
        # Perform Secure Aggregation
        # Update Model weights

        """ stub some variables """

        received_diffs_exceeds_min_worker = (
            True
        )  # get this from persisted server_config for model_id and self._diffs
        received_diffs_exceeds_max_worker = (
            False
        )  # get this from persisted server_config for model_id and self._diffs
        cycle_ended = (
            True
        )  # check cycle.cycle_time (but we should probably track cycle startime too)
        ready_to_avarege = (
            True
            if (
                (received_diffs_exceeds_max_worker or cycle_ended)
                and received_diffs_exceeds_min_worker
            )
            else False
        )
        no_protocol = True  # only deal with plans for now

        """ end variable stubs """

        if ready_to_avarege and no_protocol:
            # may need to deserialize
            _diff_state = diff
            _average_plan_diffs(model_id, _diff_state)
            # assume _diff_state produced the same as here
            # https://github.com/OpenMined/PySyft/blob/ryffel/syft-core/examples/experimental/FL%20Training%20Plan/Execute%20Plan.ipynb
            # see step 7

        response[CYCLE.STATUS] = "success"
    except Exception as e:  # Retrieve exception messages such as missing JSON fields.
        response[RESPONSE_MSG.ERROR] = str(e)

    return json.dumps(response)


from syft.execution.state import State
from syft.frameworks.torch.tensors.interpreters.placeholder import PlaceHolder
import random
import numpy as np
from syft.serde import protobuf


def _average_plan_diffs(model_id, _diff_state):
    """ TODO @Maddie: stub
            Plan only
            - get cycle
            - check hash?
            - track how many has reported successfully
            - (add diffs) list of (worker_id, diff_from_this_worker)
            - check if we have enough diffs? vs. max_worker
            - if enough diffs => average every param => save as new model value => M_prime (save params new values)
            - create new fl_process with M_prime
                new_model = processes.create_process(
                    model=serialized_M_prime,
                    client_plans=serialized_client_plans,
                    client_protocols=serialized_client_protocols,
                    server_averaging_plan=serialized_avg_plan,
                    client_config=client_config,
                    server_config=server_config,
                )
            - create new processes.create_cycle(model_id: new_model.id, version: str => same as previous version, cycle_time: int = 2500)
            - at this point new workers can join because a cycle for a model exists

    """

    _model = processes[model_id]  # de-seriallize if needed
    _model_params = _model.get_params()
    _cycle = processes.get_cycle(model_id, _model.client_config.version)

    if len(_cycle.diffs) > _model.server_config.max_worker:
        # random select max
        index_to_average = random.sample(
            range(len(_cycle.diffs)), _model.server_config.max_workerk
        )

    _updated_model_params = {
        model_param: np.mean(_cycle.diffs[diff_from_worker][model_param])
        for diff_from_worker in index_to_average
        for model_param in _model_params
    }

    local_worker = None  # should be this pygrid instance, or do we not need it?

    model_params_state = State(
        owner=local_worker,
        state_placeholders=[
            PlaceHolder().instantiate(_updated_model_params[param])
            for param in _updated_model_params
        ],
    )
    pb = protobuf.serde._bufferize(local_worker, model_params_state)
    serialized_state = pb.SerializeToString()

    # TODO @Maddie make new fl_process with new model and fl_cycle here (confirm with patrick first)
