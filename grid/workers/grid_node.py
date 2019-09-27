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

monkey.patch_all()
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

    def __str__(self):
        return "<GridNode id: " + self.id + "#objects: " + str(len(self._objects)) + ">"
