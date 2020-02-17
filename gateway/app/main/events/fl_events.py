import uuid
import json

from .socket_handler import SocketHandler
from ..codes import MSG_FIELD, RESPONSE_MSG, CYCLE
from ..processes import processes

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
        fl_process = processes.create_process(
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

        # TODO:
        # Create a new User/Worker instance to map and manage this worker.

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

        # TODO:
        # Search/Identify worker id
        # Search/Identify model id
        # Check worker health (ping/download/upload rate)
        # If available,  add this worker on fd cycle

        fl_process_id = uuid.uuid4()

        # Retrieve Cycle instance
        cycle = processes.get_cycle(model_id)

        # If doesn't exist, create a new one.
        if not cycle:
            cycle = processes.create_cycle(model_id, fl_process_id)

        ### MOCKUP ###

        # Build response
        if cycle.insert(worker_id):
            # If worker_id doesn't exist in the current cycle, insert it and return True.
            response[CYCLE.STATUS] = "accepted"
            response[MSG_FIELD.MODEL] = "my-federated-model"
            response[CYCLE.VERSION] = version
            response[CYCLE.KEY] = cycle.new_hash(worker_id)
            response[CYCLE.PLANS] = {}
            response[CYCLE.PROTOCOLS] = {}
            response[CYCLE.CLIENT_CONFIG] = {}
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

        response[CYCLE.STATUS] = "success"
    except Exception as e:  # Retrieve exception messages such as missing JSON fields.
        response[RESPONSE_MSG.ERROR] = str(e)

    return json.dumps(response)
