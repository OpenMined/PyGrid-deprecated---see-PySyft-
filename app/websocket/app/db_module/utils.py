from .models import Worker as WorkerMDL
from .models import WorkerObject
from .models import db


def snapshot(worker):
    """ Persist workers to our persistence layer """
    db.session.query(WorkerObject).filter_by(worker_id=worker.id).delete()
    objects = [
        WorkerObject(worker_id=worker.id, object=obj, id=key)
        for key, obj in worker._objects.items()
    ]
    result = db.session.add_all(objects)
    db.session.commit()


def recover_objects(hook):
    """ Find or create a worker by public_id """
    worker = hook.local_worker
    worker_mdl = WorkerMDL.query.filter_by(id=worker.id).first()
    if worker_mdl:
        objs = db.session.query(WorkerObject).filter_by(worker_id=worker.id).all()
        obj_dict = {}
        for obj in objs:
            obj_dict[obj.id] = obj.object
        worker._objects = obj_dict
    else:
        worker_mdl = WorkerMDL(id=worker.id)
        db.session.add(worker_mdl)
        db.session.commit()
    return worker
