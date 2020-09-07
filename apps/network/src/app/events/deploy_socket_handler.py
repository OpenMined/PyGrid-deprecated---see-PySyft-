import json
import os

import boto3

from ..workers.worker_new import Worker


class SocketHandler:
    """Handles and manages websocket connections."""

    def __init__(self, table_name, callback_url):
        self._connections_table = boto3.resource("dynamodb").Table(table_name)
        self._apigwManagementApi = boto3.client(
            "apigatewaymanagementapi", endpoint_url=callback_url
        )
        self.connections = self._get_connections()

        self._event_handlers = {
            "$connect": self._new_connection,
            "$disconnect": self._remove_connection,
            "sendMessage": self._send_msg,
        }

    def handle_event(self, event):
        action = event["requestContext"]["action"]
        self._event_handlers[action](event)

    def _get_connections(self):
        """Scans the dynamoDB table and retrieves all the connections.

        Returns:
            connections: List of UUID strings representing connected worker's id
        """
        response = self._connections_table.scan()["Items"]
        connections = [item["workerId"] for item in response]
        return connections

    def _new_connection(self, event):
        """Add a new connection.

        Args:
            event: dict
        """
        workerId = event["requestContext"]["connectionId"]
        try:
            self._connections_table.put_Item(Item={"workerId": workerId})
            self.connections.append(workerId)
        except Exception as e:  # Todo: change this to handle only duplicate id exception
            print(e)
        worker = Worker(workerId)
        return worker

    def _send_msg(self, event):
        """Send messages to the given worker.

        Args:
            event: dict
        """
        workerId = event["requestContext"]["connectionId"]
        message = json.loads(event["body"])["message"]
        if workerId in self.connections:
            self._apigwManagementApi.post_to_connection(
                ConnectionId=workerId, Data=bytes(message, "utf-8")
            )

    def get(self, query):
        """Retrieve a worker by its UUID string."""
        if query in self.connections:
            return Worker(query)

    def _remove_connection(self, event):
        """Removes the connection, when the socket connection is closed.

        Args:
            workerId: UUID string used to identify worker.
        """
        workerId = event["requestContext"]["connectionId"]
        try:
            self._connections_table.delete_Item(Key={"workerId": workerId})
            self.connections.remove(workerId)
        except Exception as e:  # Todo: change this to handle only specific exceptions
            print(e)

    @property
    def nodes(self):
        """Return all the connected nodes as a list of tuples of (worker_id,
        worker)"""
        return [Worker(workerId) for workerId in self.connections]

    def __len__(self):
        """Number of connections handled by this server.

        Returns:
            length: number of connections handled by this server.
        """
        return len(self.connections)


websocket_invoke_url = str(os.environ.get("WEBSOCKET_INVOKE_URL"))
socket_handler = SocketHandler(
    table_name=os.environ.get("DYNAMODB_TABLE_NAME"),
    callback_url=websocket_invoke_url.replace("wss", "https"),
)


def lambda_handler(event, context):
    socket_handler.handle_event(event)
    return {"statusCode": 200}
