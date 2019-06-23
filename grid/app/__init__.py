from flask import Flask
from flask import session, request

from flask_migrate import Migrate
import binascii
import syft as sy
import torch as th
from flask_sqlalchemy import SQLAlchemy

hook = sy.TorchHook(th)
db = SQLAlchemy()
from .models import Worker as WorkerMDL
from .models import WorkerObject

def _maybe_create_worker(worker_name: str = "worker", virtual_worker_id: str = "grid"):
    worker_mdl = WorkerMDL.query.filter_by(public_id=worker_name).first()
    if worker_mdl is None:
        worker_mdl = WorkerMDL(public_id=worker_name)
        db.session.add(worker_mdl)
        db.session.commit()
        worker = sy.VirtualWorker(hook, virtual_worker_id, auto_add=False)
        print("\t \nCREATING NEW WORKER!!")
    else:
        worker = sy.VirtualWorker(hook, virtual_worker_id, auto_add=False)
        for obj in worker_mdl.worker_objects:
            print("ADDING", obj)
            worker.register_obj(obj.object)
        print("\t \nFOUND OLD WORKER!! " + str(worker._objects.keys()))
    return worker, worker_mdl


def _request_message(worker):
    message = request.form["message"]
    message = binascii.unhexlify(message[2:-1])
    response = worker._recv_msg(message)
    response = str(binascii.hexlify(response))
    return response


def _store_worker(worker, worker_mdl: WorkerMDL, worker_name: str = "worker"):
    db.session.query(WorkerObject).filter_by(worker_id=worker_mdl.id).delete()
    objects = [WorkerObject(worker_id=worker_mdl.id, object=obj) for key,obj in worker._objects.items()]
    result = db.session.add_all(objects)
    db.session.commit()

def create_app(test_config=None):

    app = Flask(__name__)
    migrate = Migrate(app, db)
    if test_config is None:
        # TODO: move to configuration
        db_url="postgresql://postgres:password@localhost:5432/grid_example_dev"
        app.config.from_mapping(
            SQLALCHEMY_DATABASE_URI=db_url,
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )

    else:
        # load the test config if passed in
        app.config['SQLALCHEMY_DATABASE_URI'] = test_config['SQLALCHEMY_DATABASE_URI']
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



    db.init_app(app)

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
            worker, worker_mdl = _maybe_create_worker("worker", "grid")
            worker.verbose = True
            sy.torch.hook.local_worker.add_worker(worker)
            response = _request_message(worker)
            print("\t NEW WORKER STATE:" + str(worker._objects.keys()) + "\n\n")
            _store_worker(worker, worker_mdl, "worker")
            db.session.flush()
            return response
        except Exception as e:
            return str(e)

    app.add_url_rule('/', endpoint='index')
    return app
