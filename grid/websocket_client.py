import binascii
import json
import os
import requests
from requests_toolbelt.multipart import encoder, decoder
import sys

from typing import List, Union
from urllib.parse import urlparse

import websocket
import torch
from gevent import monkey

import syft as sy
from syft.messaging.message import Message, PlanCommandMessage
from syft.generic.tensor import AbstractTensor
from syft.workers.base import BaseWorker
from syft import WebsocketClientWorker
from syft.federated.federated_client import FederatedClient
from syft.codes import MSGTYPE
from syft.messaging.message import Message

from grid import utils as gr_utils
from grid.auth import search_credential

MODEL_LIMIT_SIZE = (1024 ** 2) * 64  # 64MB


class WebsocketGridClient(WebsocketClientWorker, FederatedClient):
    """Websocket Grid Client."""

    def __init__(
        self,
        hook,
        address,
        id: Union[int, str] = 0,
        auth: dict = None,
        is_client_worker: bool = False,
        log_msgs: bool = False,
        verbose: bool = False,
        data: List[Union[torch.Tensor, AbstractTensor]] = None,
        chunk_size: int = MODEL_LIMIT_SIZE,
    ):
        """
        Args:
            hook : a normal TorchHook object
            address : the address this client connects to
            id : the unique id of the worker (string or int)
            auth : An optional dict parameter give authentication credentials,
                to perform authentication process during node connection process.
                If not defined, we'll work with a public grid node version, otherwise,
                we'll work with a private version of the same grid node.
            is_client_worker : An optional boolean parameter to indicate
                whether this worker is associated with an end user client. If
                so, it assumes that the client will maintain control over when
                variables are instantiated or deleted as opposed to handling
                tensor/variable/model lifecycle internally. Set to True if this
                object is not where the objects will be stored, but is instead
                a pointer to a worker that eists elsewhere.
                log_msgs : whether or not all messages should be
                saved locally for later inspection.
            verbose : a verbose option - will print all messages
                sent/received to stdout
            data : any initial tensors the server should be
                initialized with (such as datasets)
        """
        self.address = address

        # Parse address string to get scheme, host and port
        self.secure, self.host, self.port = self.parse_address(address)

        # Initialize WebsocketClientWorker / Federated Client
        super().__init__(
            hook,
            self.host,
            self.port,
            self.secure,
            id,
            is_client_worker,
            log_msgs,
            verbose,
            data,
        )

        # Update Node reference using node's Id given by the remote grid node
        self._update_node_reference(self.get_node_id())
        self.credentials = None

        # If auth mode enabled, perform authentication
        if auth:
            self.authenticate(auth)

        self._encoding = "ISO-8859-1"
        self._chunk_size = chunk_size

    @property
    def url(self):
        if self.port:
            return (
                f"wss://{self.host}:{self.port}"
                if self.secure
                else f"ws://{self.host}:{self.port}"
            )
        else:
            return self.address

    def _update_node_reference(self, new_id: str):
        """ Update worker references changing node id references at hook structure.
            
            Args:
                new_id (String) : New worker ID.
        """
        del self.hook.local_worker._known_workers[self.id]
        self.id = new_id
        self.hook.local_worker._known_workers[new_id] = self

    def parse_address(self, address: str):
        """ Parse Address string to define secure flag and split into host and port.
            
            Args:
                address (String) : Adress of remote worker.
        """
        url = urlparse(address)
        secure = True if url.scheme == "wss" else False
        return (secure, url.hostname, url.port)

    def get_node_id(self):
        """ Get Node ID from remote node worker
            
            Returns:
                node_id (String) : node id used by remote worker.
        """
        message = {"type": "get-id"}
        response = self._forward_json_to_websocket_server_worker(message)
        return response.get("id", None)

    def connect_nodes(self, node):
        """ Connect two remote workers between each other.
            If this node is authenticated, use the same credentials to authenticate the candidate node.
            
            Args:
                node (WebsocketGridClient) : Node that will be connected with this remote worker.
            Returns:
                node_response (Dict) : node response.
        """
        message = {"type": "connect-node", "address": node.address, "id": node.id}
        if node.credentials:
            message["auth"] = node.credentials
        return self._forward_json_to_websocket_server_worker(message)

    def authenticate(self, user):
        """ Perform Authentication Process using credentials grid credentials.
            Grid credentials can be loaded calling the function gr.load_auth_credentials().

            Args:
                user : String containing the username of a loaded credential or a credential's dict.
        """
        cred_dict = None
        # If user is a string
        if isinstance(user, str):
            cred = search_credential(user)
            cred_dict = cred.json()
        # If user is a dict structure
        elif isinstance(user, dict):
            cred_dict = user

        if cred_dict:
            # Prepare a authentication request to remote grid node
            cred_dict["type"] = "authentication"
            response = self._forward_json_to_websocket_server_worker(cred_dict)
            # If succeeded, update node's reference and update client's credential.
            node_id = self._return_bool_result(response, "node_id")
            if node_id:
                self._update_node_reference(node_id)
                self.credentials = cred_dict
        else:
            raise RuntimeError("Invalid user.")

    def _forward_json_to_websocket_server_worker(self, message: dict) -> dict:
        """ Prepare/send a JSON message to a remote grid node and receive the response.
            
            Args:
                message (Dict) : message payload.
            Returns:
                node_response (Dict) : response payload.
        """
        self.ws.send(json.dumps(message))
        return json.loads(self.ws.recv())

    def _forward_to_websocket_server_worker(self, message: bin) -> bin:
        """ Prepare/send a binary message to a remote grid node and receive the response.
            Args:
                message (bytes) : message payload.
            Returns:
                node_response (bytes) : response payload.
        """
        self.ws.send_binary(message)
        response = self.ws.recv()
        return response

    def serve_model(
        self,
        model,
        model_id: str = None,
        allow_download: bool = False,
        allow_remote_inference: bool = False,
    ):
        """ Hosts the model and optionally serve it using a Socket / Rest API.
            
            Args:
                model: A jit model or Syft Plan.
                model_id: An integer or string representing the model id used to retrieve the model
                    later on using the Rest API. If this is not provided and the model is a Plan
                    we use model.id, if the model is a jit model we raise an exception.
                allow_download: If other workers should be able to fetch a copy of this model to run it locally set this to True.
                allow_remote_inference: If other workers should be able to run inference using this model through a Rest API interface set this True.
            Returns:
                True if model was served sucessfully, raises a RunTimeError otherwise.
            Raises:
                ValueError: if model_id is not provided and model is a jit model (aka does not have an id attribute).
                RunTimeError: if there was a problem during model serving.
        """
        if model_id is None:
            if isinstance(model, sy.Plan):
                model_id = model.id
            else:
                raise ValueError("Model id argument is mandatory for jit models.")

        # If the model is a Plan we send the model
        # and host the plan version created after
        # the send operation
        if isinstance(model, sy.Plan):
            # We need to use the same id in the model
            # as in the POST request.
            model.id = model_id
            model.send(self)
            model.ptr_plans[self.id].garbage_collect_data = False
            res_model = model.ptr_plans[self.id]
        else:
            res_model = model

        # Send post
        serialized_model = sy.serde.serialize(res_model)

        # If the model is smaller than a chunk size
        if sys.getsizeof(serialized_model) <= self._chunk_size:
            message = {
                "type": "host-model",
                "encoding": self._encoding,
                "model_id": model_id,
                "allow_download": str(allow_download),
                "allow_remote_inference": str(allow_remote_inference),
                "model": serialized_model.decode(self._encoding),
            }
            response = self._forward_json_to_websocket_server_worker(message)
        else:
            # HUGE Models
            # TODO: Replace to websocket protocol
            response = json.loads(
                self._send_streaming_post(
                    "serve-model/",
                    data={
                        "model": (
                            model_id,
                            serialized_model,
                            "application/octet-stream",
                        ),
                        "encoding": self._encoding,
                        "model_id": model_id,
                        "allow_download": str(allow_download),
                        "allow_remote_inference": str(allow_remote_inference),
                    },
                )
            )
        return self._return_bool_result(response)

    def run_remote_inference(self, model_id, data, N: int = 1):
        """ Run a dataset inference using a remote model.
            
            Args:
                model_id (String) : Model ID.
                data (Tensor) : dataset to be inferred.
            Returns:
                inference (Tensor) : Inference result
            Raises:
                RuntimeError : If an unexpected behavior happen, It will forward the error message.
        """
        serialized_data = sy.serde.serialize(data).decode(self._encoding)
        message = {
            "type": "run-inference",
            "model_id": model_id,
            "data": serialized_data,
            "encoding": self._encoding,
        }
        response = self._forward_json_to_websocket_server_worker(message)
        return self._return_bool_result(response, "prediction")

    def search(self, *query):
        """ Search datasets references using their tags (AND Operation).

            Args:
                query: Set of dataset tags.
            Returns:
                match_datasets (List) : List of tensors with result datasets.
        """
        # Prepare a message requesting the websocket server to search among its objects
        message = Message(MSGTYPE.SEARCH, query)
        serialized_message = sy.serde.serialize(message)

        # Send the message and return the deserialized response.
        response = self._recv_msg(serialized_message)
        return sy.serde.deserialize(response)

    def _return_bool_result(self, result, return_key=None):
        if result["success"]:
            return result[return_key] if return_key is not None else True
        elif result["error"]:
            raise RuntimeError(result["error"])
        else:
            raise RuntimeError(
                "Something went wrong, check the server logs for more information."
            )

    def _send_http_request(
        self,
        route,
        data,
        request,
        N: int = 10,
        unhexlify: bool = True,
        return_response_text: bool = True,
    ):
        """Helper function for sending http request to talk to app.

            Args:
                route: App route.
                data: Data to be sent in the request.
                request: Request type (GET, POST, PUT, ...).
                N: Number of tries in case of fail. Default is 10.
                unhexlify: A boolean indicating if we should try to run unhexlify on the response or not.
                return_response_text: If True return response.text, return raw response otherwise.
            Returns:
                If return_response_text is True return response.text, return raw response otherwise.
        """
        url = (
            f"https://{self.host}:{self.port}"
            if self.secure
            else f"http://{self.host}:{self.port}"
        )
        url = os.path.join(url, "{}".format(route))
        r = request(url, data=data) if data else request(url)
        r.encoding = self._encoding
        response = r.text if return_response_text else r

        # Try to request the message `N` times.
        for _ in range(N):
            try:
                if unhexlify:
                    response = binascii.unhexlify(response[2:-1])
                return response
            except:
                if self.verbose:
                    print(response)
                response = None
                r = request(url, data=data) if data else request(url)
                response = r.text

        return response

    def _send_streaming_post(self, route, data=None):
        """ Used to send large models / datasets using stream channel.

            Args:
                route : Service endpoint
                data : tensors / models to be uploaded.
            Returns:
                response : response from server
        """
        # Build URL path
        url = os.path.join(self.address, "{}".format(route))

        # Send data
        session = requests.Session()
        form = encoder.MultipartEncoder(data)
        headers = {"Prefer": "respond-async", "Content-Type": form.content_type}
        resp = session.post(url, headers=headers, data=form)
        session.close()
        return resp.content

    def _send_get(self, route, data=None, **kwargs):
        return self._send_http_request(route, data, requests.get, **kwargs)

    @property
    def models(self, N: int = 1):
        """ Get models stored at remote grid node.
            
            Returns:
                models (List) : List of models stored in this grid node.
        """
        message = {"type": "list-models"}
        response = self._forward_json_to_websocket_server_worker(message)
        return response["models"]

    def delete_model(self, model_id: str):
        """ Delete a model previously registered.
            
            Args:
                model_id (String) : ID of the model that will be deleted.
        """
        message = {"type": "delete-model", "model_id": model_id}
        response = self._forward_json_to_websocket_server_worker(message)
        return self._return_bool_result(response)

    def download_model(self, model_id: str):
        """ Download a model to run it locally.
        
            Args:
                model_id (String) : ID of the model that will be downloaded.
            Returns:
                model : Desired model.
            Raises:
                If an unexpected behavior happen, It will forward the error message.
        """

        def _is_large_model(result):
            return "multipart/form-data" in result.headers["Content-Type"]

        # Check if we can get a copy of this model
        # TODO: We should remove this endpoint and verify download permissions during /get_model request / fetch_plan.
        # If someone performs request/fetch outside of this function context, they'll get the model.
        result = json.loads(
            self._send_get("is_model_copy_allowed/{}".format(model_id), unhexlify=False)
        )

        if not result["success"]:
            raise RuntimeError(result["error"])

        try:
            # If the model is a plan we can just call fetch
            return sy.hook.local_worker.fetch_plan(model_id, self, copy=True)
        except AttributeError:
            # Try download model by websocket channel
            message = {"type": "download-model", "model_id": model_id}
            response = self._forward_json_to_websocket_server_worker(message)

            # If we can download model (small models) by sockets
            if response.get("serialized_model", None):
                serialized_model = result["serialized_model"].encode(self._encoding)
                model = sy.serde.deserialize(serialized_model)
                return model

            # If it isn't possible, try download model by HTTP protocol
            # TODO: This flow need to be removed when sockets can download huge models
            result = self._send_get(
                "get_model/{}".format(model_id),
                unhexlify=False,
                return_response_text=False,
            )
            if result:
                if _is_large_model(result):
                    # If model is large, receive it by a stream channel
                    multipart_data = decoder.MultipartDecoder.from_response(result)
                    model_bytes = b"".join(
                        [part.content for part in multipart_data.parts]
                    )
                    serialized_model = model_bytes.decode("utf-8").encode(
                        self._encoding
                    )
                else:
                    # If model is small, receive it by a standard json
                    result = json.loads(result.text)
                    serialized_model = result["serialized_model"].encode(self._encoding)

                model = sy.serde.deserialize(serialized_model)
                return model
            else:
                raise RuntimeError(
                    "There was a problem while getting the model, check the server logs for more information."
                )

    def serve_encrypted_model(self, encrypted_model: sy.messaging.plan.Plan):
        """Serve a model in a encrypted fashion using SMPC.

            A wrapper for sending the model. The worker is responsible for sharing the model using SMPC.

            Args:
                encrypted_model: A pĺan already shared with workers using SMPC.

            Returns:
                True if model was served successfully, raises a RunTimeError otherwise.
        """
        # Send the model
        encrypted_model.send(self)
        res_model = encrypted_model.ptr_plans[self.id]

        # Serve the model so we can have a copy saved in the database
        serialized_model = sy.serde.serialize(res_model).decode(self._encoding)
        result = self.serve_model(
            serialized_model,
            res_model.id,
            allow_download=True,
            allow_remote_inference=False,
        )
        return result

    def __str__(self):
        return "Grid Worker < id: " + self.id + " >"
