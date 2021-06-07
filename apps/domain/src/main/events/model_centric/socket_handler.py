# stdlib
import queue

from flask_sockets import Sockets
from typing import TypeVar, Type

T = TypeVar("T")


class Singleton(type):
    _instances = {}

    def __call__(cls: T, *args, **kwargs) -> Type[T]:
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SocketHandler(metaclass=Singleton):
    """Socket Handler is a singleton class used to handle/manage websocket
    connections."""

    def __init__(self) -> None:
        self.connections = {}

    def new_connection(self, workerId: str, socket: Sockets) -> None:
        """Create a mapping structure to establish a bond between a workerId
        and a socket descriptor.

        Args:
            workerId: Uuid string used to identify workers.
            socket: Socket descriptor that will be used to send/receive messages from this client.
        """
        if workerId not in self.connections:
            self.connections[workerId] = socket

    def send_msg(self, workerId: str, message: str) -> None:
        """Find the socket descriptor mapped by workerId and send them a
        message.

        Args:
            workerId: Uiid used to identify and map workers.
            message: Message that will be send.
        """
        socket = self.connections.get(workerId, None)
        if socket:
            socket.send(message)

    def remove(self, socket: Sockets) -> str:
        """Remove a socket descriptor from mapping structure. It will be used
        when the socket connection is closed.

        Args:
            socket: socket descriptor used to send/receive messages.
        Returns:
            workerId: Worker id linked to that connection.
        """
        for worker_id, skt in self.connections.items():
            if skt == socket:
                del self.connections[worker_id]
            return worker_id

    def __len__(self) -> int:
        """Number of connections handled by this server.

        Returns:
            length : number of connections handled by this server.
        """
        return len(self.connections)
