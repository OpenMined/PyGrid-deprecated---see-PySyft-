import syft as sy
import torch as th
import json
import sys
from syft.codes import RESPONSE_MSG
from syft.generic.pointers.pointer_tensor import PointerTensor
from .. import local_worker, hook
from ..persistence import model_controller
from ..persistence.object_storage import recover_objects
from flask_login import current_user
from ..auth import authenticated_only

MODEL_LIMIT_SIZE = (1024 ** 2) * 64  # 64MB


@authenticated_only
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
    mpc = message["mpc"] == "True"
    serialized_model = message["model"]

    # Encode the model accordingly
    serialized_model = serialized_model.encode(encoding)

    # save the model for later usage
    response = model_controller.save(
        current_user.worker,
        serialized_model,
        model_id,
        allow_download,
        allow_remote_inference,
        mpc,
    )
    return json.dumps(response)


@authenticated_only
def delete_model(message: dict) -> str:
    """ Delete a model previously stored at database.

        Args:
            message (dict) : Model's id.
        Returns:
            response (str) : Node's response.
    """
    model_id = message["model_id"]
    result = model_controller.delete(current_user.worker, model_id)
    return json.dumps(result)


@authenticated_only
def get_models(message: dict) -> str:
    """ Get a list of stored models.

        Returns:
            response (str) : List of models stored at this node.
    """
    model_list = model_controller.models(current_user.worker)
    return json.dumps(model_list)


def download_model(message: dict) -> str:
    """ Download a specific model stored at this node.

        Args:
            message (dict) : Model's id.
        Returns:
            response (str) : Node's response with serialized model.
    """
    model_id = message["model_id"]

    # If not Allowed
    check = False  # mm.is_model_copy_allowed(model_id)
    response = {}
    if not check[RESPONSE_MSG.SUCCESS]:  # If not allowed
        if check[RESPONSE_MSG.ERROR] == "Message":  # mm.MODEL_NOT_FOUND_MSG:
            status_code = 404  # Not Found
            response[RESPONSE_MSG.ERROR] = "Message"  # mm.Model_NOT_FOUND_MSG
        else:
            status_code = 403  # Forbidden
            response[RESPONSE_MSG.ERROR] = "Message"  # mm.NOT_ALLOWED_TO_DOWNLOAD_MSG
        response[RESPONSE_MSG.SUCCESS] = False
        return json.dumps(response)

    # If allowed
    result = {}  # mm.get_serialized_model_with_id(model_id)

    if result[RESPONSE_MSG.SUCCESS]:
        # Use correct encoding
        response = {"serialized_model": result["serialized_model"].decode("ISO-8859-1")}
        if sys.getsizeof(response["serialized_model"]) >= MODEL_LIMIT_SIZE:
            # Forward to HTTP method
            # TODO: Implement download of huge models using sockets
            return json.dumps({RESPONSE_MSG.SUCCESS: False})
        else:
            return json.dumps(response)


@authenticated_only
def run_inference(message: dict) -> str:
    """ Run dataset inference with a specifc model stored in this node.

        Args:
            message (dict) : Serialized dataset, model id and dataset's metadata.
        Returns:
            response (str) : Model's inference.
    """
    ## If worker is empty, load previous database tensors.
    if not current_user.worker._objects:
        recover_objects(current_user.worker)

    response = model_controller.get(current_user.worker, message["model_id"])

    if response[RESPONSE_MSG.SUCCESS]:

        # If model exists but not allow remote inferences
        if not response["model_properties"]["allow_remote_inference"]:
            return json.dumps(
                {
                    RESPONSE_MSG.SUCCESS: False,
                    "not_allowed": True,
                    RESPONSE_MSG.ERROR: "You're not allowed to run inferences on this model.",
                }
            )

        model = response["model_properties"]["model"]

        # serializing the data from GET request
        encoding = message["encoding"]
        serialized_data = message["data"].encode(encoding)
        data = sy.serde.deserialize(serialized_data)

        # If we're using a Plan we need to register the object
        # to the local worker in order to execute it
        current_user.worker._objects[data.id] = data

        # Some models returns tuples (GPT-2 / BERT / ...)
        # To avoid errors on detach method, we check the type of inference's result
        model_output = model(data)

        # It the model is a plan, it'll receive a tensor wrapper as a model_output.
        while model_output.is_wrapper or isinstance(model_output, PointerTensor):
            model_output = model_output.get()

        if isinstance(model_output, tuple):
            predictions = model_output[0].detach().numpy().tolist()
        else:
            predictions = model_output.detach().numpy().tolist()

        # We can now remove data from the objects
        del data
        return json.dumps(
            {RESPONSE_MSG.SUCCESS: True, RESPONSE_MSG.INFERENCE_RESULT: predictions}
        )
    else:
        return json.dumps(response)
