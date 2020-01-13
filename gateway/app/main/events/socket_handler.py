import queue


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SocketHandler(metaclass=Singleton):
    def __init__(self):
        self.connections = {}

    def new_connection(self, workerId, socket):
        if workerId not in self.connections:
            self.connections[workerId] = socket

    def send_msg(self, workerId, message):
        socket = self.connections.get(workerId, None)
        if socket:
            socket.send(message)

    def remove(self, socket):
        for worker_id, skt in self.connections.items():
            if skt == socket:
                del self.connections[worker_id]
            return worker_id

    def __len__(self):
        return len(self.connections)
