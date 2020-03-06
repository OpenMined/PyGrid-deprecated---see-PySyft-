import torch as th
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import binascii
import syft as sy

import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_sockets import Sockets
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


# Default secret key used only for testing / development
DEFAULT_SECRET_KEY = "justasecretkeythatishouldputhere"


def set_database_config(app, test_config=None, verbose=False):
    """ Set configs to use SQL Alchemy library.

        Args:
            app: Flask application.
            test_config : Dictionary containing SQLAlchemy configs for test purposes.
            verbose : Level of flask application verbosity.
        Returns:
            app: Flask application.
        Raises:
            RuntimeError : If DATABASE_URL or test_config didn't initialized, RuntimeError exception will be raised.
    """
    global db
    db_url = os.environ.get("DATABASE_URL", "sqlite:///databaseGateway.db")
    migrate = Migrate(app, db)
    if test_config is None:
        if db_url:
            app.config.from_mapping(
                SQLALCHEMY_DATABASE_URI=db_url, SQLALCHEMY_TRACK_MODIFICATIONS=False
            )
        else:
            raise RuntimeError(
                "Invalid database address : Set DATABASE_URL environment var or add test_config parameter at create_app method."
            )
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = test_config["SQLALCHEMY_DATABASE_URI"]
        app.config["TESTING"] = (
            test_config["TESTING"] if test_config.get("TESTING") else True
        )
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = (
            test_config["SQLALCHEMY_TRACK_MODIFICATIONS"]
            if test_config.get("SQLALCHEMY_TRACK_MODIFICATIONS")
            else False
        )
    app.config["VERBOSE"] = verbose
    db.init_app(app)
    return app


def create_app(debug=False, n_replica=None, test_config=None):
    """Create flask application."""
    app = Flask(__name__)
    app.debug = debug

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", None)

    if app.config["SECRET_KEY"] is None:
        app.config["SECRET_KEY"] = DEFAULT_SECRET_KEY
        logging.warn(
            "Using default secrect key, this is not safe and should be used only for testing and development. To define a secrete key please define the environment variable SECRET_KEY."
        )

    app.config["N_REPLICA"] = n_replica

    from main import main as main_blueprint, ws
    from main import db

    global db
    sockets = Sockets(app)

    # Set SQLAlchemy configs
    app = set_database_config(app, test_config=test_config)
    s = app.app_context().push()
    db.create_all()

    # Register app blueprints
    app.register_blueprint(main_blueprint)
    sockets.register_blueprint(ws, url_prefix=r"/")

    CORS(app)
    return app


app = create_app()
from syft.serde.serde import serialize, deserialize


# async def test_fl_process(self):
#         """ 1 - Host Federated Training """
#         # Plan Functions
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
#         serialized_plan_method_2 = binascii.hexlify(serialize(foo_2)).decode()
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
            #             "foo_2": serialized_plan_method_2,
        },
        "protocols": {"protocol_1": "serialized_protocol_mockup"},
        "averaging_plan": serialized_avg_plan,
        "client_config": client_config,
        "server_config": server_config,
    },
}

# Send host_training message
#         response = await send_ws_message(host_training_message)
#         self.assertEqual(response, {"status": "success"})

from main.processes import processes

processes.create_process(
    model,
    host_training_message["data"]["plans"],
    client_config,
    server_config,
    serialized_avg_plan,
)


processes.create_cycle(model.id, '1.0.0')