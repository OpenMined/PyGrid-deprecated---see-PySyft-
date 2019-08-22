from flask import Blueprint
from flask import session, request
from .models import Worker as WorkerMDL
from .models import WorkerObject
from .models import db
import binascii
import torch as th
import syft as sy


def store_worker(worker, worker_mdl: WorkerMDL, worker_name: str = "worker"):
    """
    Persist workers to our persistence layer
    """
    db.session.query(WorkerObject).filter_by(worker_id=worker_mdl.id).delete()
    objects = [
        WorkerObject(worker_id=worker_mdl.id, object=obj)
        for key, obj in worker._objects.items()
    ]
    result = db.session.add_all(objects)
    db.session.commit()


def recover_worker(
    worker_name: str = "worker", virtual_worker_id: str = "grid", verbose: bool = False
):
    """
    Find or create a worker by public_id

    """
    worker_mdl = WorkerMDL.query.filter_by(public_id=worker_name).first()
    if worker_mdl is None:
        worker_mdl = WorkerMDL(public_id=worker_name)
        db.session.add(worker_mdl)
        db.session.commit()
        worker = sy.VirtualWorker(hook, virtual_worker_id, auto_add=False)
        if verbose:
            print("\t \nCREATING NEW WORKER!!")
    else:
        worker = sy.VirtualWorker(hook, virtual_worker_id, auto_add=False)
        for obj in worker_mdl.worker_objects:
            worker.register_obj(obj.object)
        if verbose:
            print("\t \nFOUND OLD WORKER!! " + str(worker._objects.keys()))
    return worker, worker_mdl
