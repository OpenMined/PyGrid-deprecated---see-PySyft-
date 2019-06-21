from flask import Flask
from flask import session, request
from .config import Config
from .config import app
from .config import db

from .models import Worker as WorkerMDL
from .models import WorkerObject

from flask_migrate import Migrate
import binascii
import syft as sy
import torch as th
hook = sy.TorchHook(th)


def _maybe_create_worker(worker_name: str = "worker", virtual_worker_id: str = "grid"):

    worker_mdl = WorkerMDL.query.filter_by(public_id=worker_name).first()
    if worker_mdl is None:
        w = WorkerMDL(public_id=worker_name)
        db.session.add(w)
        db.session.commit()
        worker = sy.VirtualWorker(hook, virtual_worker_id, auto_add=False)
        print("\t \nCREATING NEW WORKER!!")
    else:
        worker = sy.serde.deserialize(worker)
        print("\t \nFOUND OLD WORKER!! " + str(worker._objects.keys()))
    return worker


def _request_message(worker):
    message = request.form["message"]
    message = binascii.unhexlify(message[2:-1])
    response = worker._recv_msg(message)
    response = str(binascii.hexlify(response))
    return response


def _store_worker(worker, worker_name: str = "worker"):
    print("STORE WORKER!", worker)
    print(worker._objects)
    worker_mdl = WorkerMDL.query.filter_by(public_id=worker_name).first()
    objects = [WorkerObject(worker=worker_mdl, object=obj) for key,obj in worker._objects.items()]
    db.session.add_all(objects)
    db.session.commit()


def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)
    migrate = Migrate(app, db)


    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)



    @app.route("/")
    def hello_world():
        name = "World"
        return "Howdy %s!" % str(name)

    @app.route("/identity/")
    def is_this_an_opengrid_node():
        """This exists because in the automation scripts which deploy nodes,
        there's an edge case where the 'node already exists' but sometimes it
        can be an app that does something totally different. So we want to have
        some endpoint which just casually identifies this server as an OpenGrid
        server."""
        return "OpenGrid"



    @app.route("/cmd/", methods=["POST"])
    def cmd():
        try:
            worker = _maybe_create_worker("worker", "grid")
            worker.verbose = True
            sy.torch.hook.local_worker.add_worker(worker)
            response = _request_message(worker)
            print("\t NEW WORKER STATE:" + str(worker._objects.keys()) + "\n\n")
            _store_worker(worker, "worker")

            return response
        except Exception as e:
            return str(e)

    app.add_url_rule('/', endpoint='index')
    return app
