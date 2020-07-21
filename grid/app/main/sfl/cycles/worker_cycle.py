# Standard python imports
import datetime

# Local imports
from ... import db


class WorkerCycle(db.Model):
    """Relation between Workers and Cycles.

    Columns:
        id (Integer, Primary Key): Worker Cycle ID.
        cycle_id (Integer, ForeignKey): Cycle Foreign key that owns this worker cycle.
        worker_id (String, ForeignKey): Worker Foreign key that owns this worker cycle.
        request_key (String): unique token that permits downloading specific Plans, Protocols, etc.
    """

    __tablename__ = "static_worker_cycle"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    request_key = db.Column(db.String())
    cycle_id = db.Column(db.Integer, db.ForeignKey("static_cycle.id"))
    worker_id = db.Column(db.String, db.ForeignKey("static_worker.id"))
    started_at = db.Column(db.DateTime(), default=datetime.datetime.utcnow())
    is_completed = db.Column(db.Boolean(), default=False)
    completed_at = db.Column(db.DateTime())
    diff = db.Column(db.LargeBinary)

    def __str__(self):
        return f"<WorkerCycle id: {self.id}, cycle: {self.cycle_id}, worker: {self.worker_id}, is_completed: {self.is_completed}>"
