import json
import re
import time
from datetime import datetime

import requests

from ..codes import MSG_FIELD, NODE_EVENTS, WORKER_PROPERTIES
from ..utils.wrappers import threaded


class Worker(object):
    """Worker class for running PySyft models for training and inference."""

    def __init__(self, id, client):
        """
    Args:
        id: ID of the worker.
    """
        self._id = id
        self._client = client
        self._ping = 0
        self._status = WORKER_PROPERTIES.ONLINE
        self.connected_nodes = {}
        self.hosted_models = {}
        self.hosted_datasets = {}
        self.cpu_percent = 0
        self.mem_usage = 0

    @property
    def status(self):
        """str: Return the status of the Worker instance."""
        try:
            response = self._client.get_connection(ConnectionId=self._id)
        except self._client.exceptions.GoneException:
            return WORKER_PROPERTIES.OFFLINE

        if self._ping < WORKER_PROPERTIES.PING_THRESHOLD:
            return WORKER_PROPERTIES.ONLINE
        else:
            return WORKER_PROPERTIES.BUSY

    @property
    def address(self):
        """str: Return the address of the Worker instance.

        #TODO: Discuss with Ionesio.
        Should I return the IP Address?
        https://sc*******c.execute-api.ap-south-1.amazonaws.com/Test/@connections
        """
        # {
        #     'ConnectedAt': datetime(2015, 1, 1),
        #     'Identity': {
        #         'SourceIp': 'string',
        #         'UserAgent': 'string'
        #     },
        #     'LastActiveAt': datetime(2015, 1, 1)
        # }
        try:
            response = self._client.get_connection(ConnectionId=self._id)
            return response["Identity"]["SourceIp"]
        except self._client.exceptions.GoneException:
            pass

        # endpoint_url = self._client.meta.endpoint_url
        # return f'{endpoint_url}/@connections/{self._id}'

    @property
    def location(self):
        """:obj:`dict` of :obj:`str`: Return the location of the Worker instance."""
        if self.address:
            url = "http://ip-api.com/json/{}".format(self.address)
            r = requests.get(url)
            result = json.loads(r.text)
            if result["status"] == "success":
                return {
                    "region": result["regionName"],
                    "country": result["country"],
                    "city": result["city"],
                }
            else:
                return {}

    def send(self, message):
        """Send a message from the Worker instance.

        Args:
            message (json) : #TODO: define the appropriate message type here
        """
        # Todo: How do we send a message form the worker? Using SocketIO? Or something else?
        pass

    # Run it in a different thread
    @threaded
    def monitor(self):
        """Monitor the worker and send JSON message across the network."""
        while self.status == WORKER_PROPERTIES.ONLINE:
            self.__begin = time.time()
            self.send(json.dumps({MSG_FIELD.TYPE: NODE_EVENTS.MONITOR}))
            time.sleep(WORKER_PROPERTIES.HEALTH_CHECK_INTERVAL)

    def update_node_infos(self, message):
        """Update information for the connected nodes, hosted models and
        datasets as well as information on CPU and memory usage."""
        if self.__begin:
            end = time.time()
            self._ping = (end - self.__begin) * 1000
            self.connected_nodes = message[MSG_FIELD.NODES]
            self.hosted_models = message[MSG_FIELD.MODELS]
            self.hosted_datasets = message[MSG_FIELD.DATASETS]
            self.cpu_percent = message[MSG_FIELD.CPU]
            self.mem_usage = message[MSG_FIELD.MEM_USAGE]
