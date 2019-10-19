import json
from . import local_worker, hook
import syft as sy
import torch as th
from .persistence.utils import recover_objects, snapshot
from .persistence import model_manager as mm
from .auth import authenticated_only, get_session
from flask_login import login_user, current_user
from grid import WebsocketGridClient
import sys

# Suport for sending big models over the wire back to a
# worker
MODEL_LIMIT_SIZE = (1024 ** 2) * 64  # 64MB


def get_node_id(message: dict) -> str:
    """ Returns node id. 
        
        Returns:
            response (str) : Response message containing node id.
    """
    return json.dumps({"id": local_worker.id})


def authentication(message: dict) -> str:
    """ Receive user credentials and performs user authentication. 
        
        Args:
            message (dict) : Dict data structure containing user credentials.
        Returns:
            response (str) : Authentication response message.
    """
    user = get_session().authenticate(message)
    # If it was authenticated
    if user:
        login_user(user)
        return json.dumps({"success": "True", "node_id": user.worker.id})
    else:
        return json.dumps({"error": "Invalid username/password!"})


def connect_grid_nodes(message: dict) -> str:
    """ Connect remote grid nodes between each other. 
        
        Args:
            message (dict) :  Dict data structure containing node_id, node address and user credentials(optional).
        Returns:
            response (str) : response message.
    """
    if message["id"] not in local_worker._known_workers:
        worker = WebsocketGridClient(
            hook, address=message["address"], id=message["id"], auth=message.get("auth")
        )
    return json.dumps({"status": "Succesfully connected."})


@authenticated_only
def socket_ping(message: dict) -> str:
    """ Ping request to check node's health state. """
    return json.dumps({"alive": "True"})


@authenticated_only
def forward_binary_message(message: bin) -> bin:
    """ Forward binary syft messages to user's workers.
    
        Args:
            message (bin) : PySyft binary message.
        Returns:
            response (bin) : PySyft binary response.
    """

    # If worker is empty, load previous database tensors
    if not current_user.worker._objects:
        recover_objects(current_user.worker)

    # Process message
    decoded_response = current_user.worker._recv_msg(message)

    # Save worker state at database
    snapshot(current_user.worker)

    return decoded_response


@authenticated_only
def syft_command(message: dict) -> str:
    """ Forward JSON syft messages to user's workers.
    
        Args:
            message (dict) : Dictionary data structure containing PySyft message.
        Returns:
            response (str) : node response.
    """
    response = local_worker._message_router[message["msg_type"]](message["content"])
    payload = sy.serde.serialize(response, force_no_serialization=True)
    return json.dumps({"type": "command-response", "response": payload})


def host_model(message: dict) -> str:
    """ Save/Store a model into database.
    
        Args:
            message (dict) : Dict containing a serialized model and model's metadata.
        Response:
            response (str) : Node's response.
    """
    encoding = message["encoding"]
    model_id = message["model_id"]
    allow_download = message["allow_download"] == "True"
    allow_remote_inference = message["allow_remote_inference"] == "True"

    serialized_model = message["model"]

    # Encode the model accordingly
    serialized_model = serialized_model.encode(encoding)

    # save the model for later usage
    response = mm.save_model(
        serialized_model, model_id, allow_download, allow_remote_inference
    )
    return json.dumps(response)


def delete_model(message: dict) -> str:
    """ Delete a model previously stored at database.
        
        Args:
            message (dict) : Model's id.
        Returns:
            response (str) : Node's response.
    """
    model_id = message["model_id"]
    result = mm.delete_model(model_id)
    return json.dumps(result)


def get_models(message: dict) -> str:
    """ Get a list of stored models.
        
        Returns:
            response (str) : List of models stored at this node.
    """
    return json.dumps(mm.list_models())


def download_model(message: dict) -> str:
    """ Download a specific model stored at this node.
        
        Args:
            message (dict) : Model's id.
        Returns:
            response (str) : Node's response with serialized model.
    """
    model_id = message["model_id"]

    # If not Allowed
    check = mm.is_model_copy_allowed(model_id)
    response = {}
    if not check["success"]:  # If not allowed
        if check["error"] == mm.MODEL_NOT_FOUND_MSG:
            status_code = 404  # Not Found
            response["error"] = mm.Model_NOT_FOUND_MSG
        else:
            status_code = 403  # Forbidden
            response["error"] = mm.NOT_ALLOWED_TO_DOWNLOAD_MSG
        response["success"] = False
        return json.dumps(response)

    # If allowed
    result = mm.get_serialized_model_with_id(model_id)

    if result["success"]:
        # Use correct encoding
        response = {"serialized_model": result["serialized_model"].decode("ISO-8859-1")}
        if sys.getsizeof(response["serialized_model"]) >= MODEL_LIMIT_SIZE:
            # Forward to HTTP method
            # TODO: Implement download of huge models using sockets
            return json.dumps({"success": False})
        else:
            return json.dumps(response)


def run_inference(message: dict) -> str:
    """ Run dataset inference with a specifc model stored in this node.
        
        Args:
            message (dict) : Serialized dataset, model id and dataset's metadata.
        Returns:
            response (str) : Model's inference.
    """
    response = mm.get_model_with_id(message["model_id"])
    if response["success"]:
        model = response["model"]

        # serializing the data from GET request
        encoding = message["encoding"]
        serialized_data = message["data"].encode(encoding)
        data = sy.serde.deserialize(serialized_data)

        # If we're using a Plan we need to register the object
        # to the local worker in order to execute it
        local_worker._objects[data.id] = data

        # Some models returns tuples (GPT-2 / BERT / ...)
        # To avoid errors on detach method, we check the type of inference's result
        model_output = model(data)
        if isinstance(model_output, tuple):
            predictions = model_output[0].detach().numpy().tolist()
        else:
            predictions = model_output.detach().numpy().tolist()

        # We can now remove data from the objects
        del data
        return json.dumps({"success": True, "prediction": predictions})
    else:
        return json.dumps(response)
