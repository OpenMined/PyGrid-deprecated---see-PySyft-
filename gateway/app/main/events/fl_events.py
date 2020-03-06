import uuid
import json
from binascii import unhexlify

from .socket_handler import SocketHandler
from ..codes import MSG_FIELD, RESPONSE_MSG, CYCLE
from ..processes import processes
from ..auth import workers
from syft.serde.serde import deserialize
from .. import hook
import traceback


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
        serialized_model = unhexlify(
            data.get(MSG_FIELD.MODEL, None).encode()
        )  # Only one
        serialized_client_plans = data.get(CYCLE.PLANS, None)  # 1 or *
        serialized_client_protocols = data.get(CYCLE.PROTOCOLS, None)  # 0 or *
        serialized_avg_plan = data.get(CYCLE.AVG_PLAN, None)  # Only one
        client_config = data.get(CYCLE.CLIENT_CONFIG, None)  # Only one
        server_config = data.get(CYCLE.SERVER_CONFIG, None)  # Only one

        model = deserialize(serialized_model)

        # Create a new FL Process
        processes.create_process(
            model=model,
            client_plans=serialized_client_plans,
            client_protocols=serialized_client_protocols,
            server_averaging_plan=serialized_avg_plan,
            client_config=client_config,
            server_config=server_config,
        )
        response[CYCLE.STATUS] = RESPONSE_MSG.SUCCESS
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

        # Create worker instance
        workers.create(worker_id)

        response[CYCLE.STATUS] = RESPONSE_MSG.SUCCESS
        response[MSG_FIELD.WORKER_ID] = worker_id
    except Exception as e:  # Retrieve exception messages such as missing JSON fields.
        response[CYCLE.STATUS] = RESPONSE_MSG.ERROR
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
        ping = int(data.get(CYCLE.PING, None))
        download = float(data.get(CYCLE.DOWNLOAD, None))
        upload = float(data.get(CYCLE.UPLOAD, None))

        # Retrieve the worker
        worker = workers.get(id=worker_id)

        worker.ping = ping
        worker.avg_download = download
        worker.avg_upload = upload
        workers.update(worker)  # Update database worker attributes

        # The last time this worker was assigned for this model/version.
        last_participation = processes.last_participation(worker_id, model_id, version)

        # Assign
        response = processes.assign(model_id, version, worker, last_participation)
    except Exception as e:
        response[CYCLE.STATUS] = CYCLE.REJECTED
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
    # data = message[MSG_FIELD.DATA]
    response = {}

    try:
        # model_id = data.get(MSG_FIELD.MODEL, None)
        # request_key = data.get(CYCLE.KEY, None)
        # diff = data.get(CYCLE.DIFF, None)

        # TODO:
        # Perform Secure Aggregation
        # Update Model weights

        response[CYCLE.STATUS] = RESPONSE_MSG.SUCCESS
    except Exception as e:  # Retrieve exception messages such as missing JSON fields.
        response[RESPONSE_MSG.ERROR] = str(e)

    return json.dumps(response)

    async def test_fl_process(self):
        """ 1 - Host Federated Training """
        # Plan Functions
        @sy.func2plan(args_shape=[(1,), (1,), (1,)])
        def foo_1(x, y, z):
            a = x + x
            b = x + z
            c = y + z
            return c, b, a

        @sy.func2plan(args_shape=[(1,), (1,), (1,)])
        def foo_2(x, y, z):
            a = x + x
            b = x + z
            return b, a

        @sy.func2plan(args_shape=[(1,), (1,)])
        def avg_plan(x, y):
            result = x + y / 2
            return result

        # Plan Model
        class Net(sy.Plan):
            def __init__(self):
                super(Net, self).__init__(id="my-model")
                self.fc1 = nn.Linear(2, 3)
                self.fc2 = nn.Linear(3, 2)
                self.fc3 = nn.Linear(2, 1)

            def forward(self, x):
                x = F.relu(self.fc1(x))
                x = self.fc2(x)
                x = self.fc3(x)
                return F.log_softmax(x, dim=0)

        model = Net()
        model.build(th.tensor([1.0, 2]))

        # Serialize plans / protocols and model
        serialized_plan_method_1 = binascii.hexlify(serialize(foo_1)).decode()
        serialized_plan_method_2 = binascii.hexlify(serialize(foo_2)).decode()
        serialized_avg_plan = binascii.hexlify(serialize(avg_plan)).decode()
        serialized_plan_model = binascii.hexlify(serialize(model)).decode()

        # As mentioned at federated learning roadmap.
        # We're supposed to set up client / server configs
        client_config = {
            "name": "my-federated-model",
            "version": "0.1.0",
            "batch_size": 32,
            "lr": 0.01,
            "optimizer": "SGD",
        }

        server_config = {
            "max_workers": 100,
            "pool_selection": "random",  # or "iterate"
            "num_cycles": 5,
            "do_not_reuse_workers_until_cycle": 4,
            "cycle_length": 8 * 60 * 60,  # 8 hours
            "minimum_upload_speed": 2,  # 2 mbps
            "minimum_download_speed": 4,  # 4 mbps
        }

        # "federated/host-training" request body
        host_training_message = {
            "type": "federated/host-training",
            "data": {
                "model": serialized_plan_model,
                "plans": {
                    "foo_1": serialized_plan_method_1,
                    "foo_2": serialized_plan_method_2,
                },
                "protocols": {"protocol_1": "serialized_protocol_mockup"},
                "averaging_plan": serialized_avg_plan,
                "client_config": client_config,
                "server_config": server_config,
            },
        }

        # Send host_training message
        response = await send_ws_message(host_training_message)
        self.assertEqual(response, {"status": "success"})
