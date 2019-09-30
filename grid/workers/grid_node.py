import binascii
import json
from typing import List, Union
from urllib.parse import urlparse

import syft as sy
import torch
import websocket
from gevent import monkey
from syft import WebsocketClientWorker
from syft.federated.federated_client import FederatedClient
from syft.generic.tensor import AbstractTensor

# monkey.patch_all()
import numpy as np


class GridNode(WebsocketClientWorker, FederatedClient):
    """ Websocket Grid Client """

    def __init__(
        self,
        hook,
        address,
        id: Union[int, str] = 0,
        is_client_worker: bool = False,
        log_msgs: bool = False,
        verbose: bool = False,
        data: List[Union[torch.Tensor, AbstractTensor]] = None,
    ):
        from websocket import create_connection

        """
        Args:
            hook : a normal TorchHook object
            addr : the address this client connects to
            log_msgs : whether or not all messages should be
                saved locally for later inspection.
            verbose : a verbose option - will print all messages
                sent/received to stdout
            data : any initial tensors the server should be
                initialized with (such as datasets)
        """
        self.address = address
        self.secure, self.host, self.port = self.parse_address(address)
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
        self.id = self.get_node_id()
        self._encoding = "ISO-8859-1"

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

    def parse_address(self, address):
        url = urlparse(address)
        secure = True if url.scheme == "wss" else False
        return (secure, url.hostname, url.port)

    def get_node_id(self):
        message = {"type": "get-id"}
        self.ws.send(json.dumps(message))
        return json.loads(self.ws.recv())["id"]

    def connect_nodes(self, node):
        message = {"type": "connect-node", "address": node.address, "id": node.id}
        self.ws.send(json.dumps(message))
        return json.loads(self.ws.recv())

    def _forward_to_websocket_server_worker(self, message: bin) -> bin:
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
            res_model = model.ptr_plans[self.id]
        else:
            res_model = model

        # Send post
        serialized_model = sy.serde.serialize(res_model).decode(self._encoding)

        self.ws.send(
            json.dumps(
                {
                    "type": "host-model",
                    "encoding": self._encoding,
                    "model_id": model_id,
                    "allow_download": str(allow_download),
                    "allow_remote_inference": str(allow_remote_inference),
                    "model": serialized_model,
                }
            )
        )
        response = json.loads(self.ws.recv())
        if response["success"]:
            return True
        else:
            raise RuntimeError(response["error"])

    def run_remote_inference(self, model_id, data, N: int = 1):
        serialized_data = sy.serde.serialize(data).decode(self._encoding)
        payload = {
            "type": "run-inference",
            "model_id": model_id,
            "data": serialized_data,
            "encoding": self._encoding,
        }
        self.ws.send(json.dumps(payload))
        response = json.loads(self.ws.recv())
        if response["success"]:
            return torch.tensor(response["prediction"])
        else:
            raise RuntimeError(response["error"])

    def __str__(self):
        return "<GridNode id: " + self.id + "#objects: " + str(len(self._objects)) + ">"
