from ... import db


class Worker(db.Model):
    """Web / Mobile worker table.

    Columns:
        id (String, Primary Key): Worker's ID.
        format_preference (String): either "list" or "ts"
        ping (Float): Ping rate.
        avg_download (Float): Download rate.
        avg_upload (Float): Upload rate.
        worker_cycles (WorkerCycle): Relationship between workers and cycles (One to many).
    """

    __tablename__ = "static_worker_"

    id = db.Column(db.String, primary_key=True)
    format_preference = db.Column(db.String())
    ping = db.Column(db.Float)
    avg_download = db.Column(db.Float)
    avg_upload = db.Column(db.Float)
    worker_cycle = db.relationship("WorkerCycle", backref="worker")

    def __str__(self):
        return f"<Worker id: {self.id}, format_preference: {self.format_preference}, ping : {self.ping}, download: {self.avg_download}, upload: {self.avg_upload}>"
