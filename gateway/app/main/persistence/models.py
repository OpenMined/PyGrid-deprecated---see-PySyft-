from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Model(db.Model):
    """ Model table that represents the AI Models.
        Columns:
            id (primary_key) : Model's id, used to recover stored model.
            version (string) : Model version.
            checkpoints (list) : Model Checkpoints.
    """

    __tablename__ = "__model__"

    id = db.Column(db.String(64), primary_key=True)
    version = db.Column(db.String(64))
    # TODO:
    # checkpoints = list(ModelCheckpoints)

    def __str__(self):
        return f"<Model  id: {self.id}, version: {self.version}>"


class ModelCheckPoint(db.Model):
    """ Model's save points.
        Columns:
            id: Checkpoint ID.
            values: Value of the model at a given checkpoint.
    """

    __tablename__ = "__model_checkpoint__"

    id = db.Column(db.String(64), primary_key=True)
    # TODO
    # values = TENSOR

    def __str__(self):
        return f"<CheckPoint id: {self.id}>"


class Plan(db.Model):
    """ Plan table that represents Syft Plans.
        Columns:
            id: Plan ID.
            value: String  (List of operations)
            value_ts: String (TorchScript)
    """

    __tablename__ = "__plan__"

    id = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(64))
    value_ts = db.Column(db.String(64))

    def __str__(self):
        return (
            f"<Plan id: {self.id}, values: {self.value}, torchscript: {self.value_ts}>"
        )


class Protocol(db.Model):
    """ Protocol table that represents Syft Protocols.
        Columns:
            id: Protocol ID.
            value: String  (List of operations)
            value_ts: String (TorchScript)
    """

    __tablename__ = "__protocol__"

    id = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(64))
    value_ts = db.Column(db.String(64))

    def __str__(self):
        return (
            f"<Plan id: {self.id}, values: {self.value}, torchscript: {self.value_ts}>"
        )


class Config(db.Model):
    """ Configs table.
        Columns:
            id: Config ID.
            value: Dictionary
    """

    id = db.Column(db.String(64), primary_key=True)
    # TODO
    # configs = Dict


class Cycle(db.Model):
    """ Cycle table.

        Columns:
            id (String):
            start (TIME): Start time.
            end (TIME): End time.
            worker_cycles:
    """

    id = db.Column(db.String(64), primary_key=True)


class WorkerCycle(db.Model):
    """ Relation between Workers and Cycles.
        Columns:
            id (String):
            fl_process_id (String):
            cycle_id (String):
            worker_id (String):
            request_key (String): unique token that permits downloading specific Plans, Protocols, etc.
    """

    id = db.Column(db.String(64), primary_key=True)
    fl_process_id = db.Column(db.String(64))
    cycle_id = db.Column(db.String(64))
    worker_id = db.Column(db.String(64))
    request_key = db.Column(db.String(64))

    def __str__(self):
        f"<WorkerCycle id: {self.id}, fl_process: {self.fl_process_id}, cycle: {self.cycle_id}, worker: {self.worker}, request_key: {self.request_key}>"


class Worker(db.Model):
    """ Web / Mobile worker table.
        Columns:
            id (String): Worker's ID.
            format_preference (String): either "list" or "ts"
            ping (Int): Ping rate.
            avg_download (Int): Download rate.
            avg_upload (Int): Upload rate.
            worker_cycles [WorkerCycles] : List of cycles used by this worker.
    """

    id = db.Column(db.String(64), primary_key=True)
    format_preference = db.Column(db.String(64))
    ping = db.Column(db.BigInteger)
    avg_download = db.Column(db.String(64))
    avg_upload = db.Column(db.String(64))
    # TODO
    # Worker Cycles (Worker)

    def __str__(self):
        return f"<Worker id: {self.id}, format_preference: {self.format_preference}, ping : {self.ping}, download: {self.download}, upload: {self.upload}>"


class FLProcess(db.Model):
    """ Federated Learning Process table.
        Columns:
            id (String):
            averaging_plan (Plan):
            plans: [
                training_plan: Plan
                validation-plan: Plan
            ]
            protocols (Protocol) :
            client_config (Config):
            server_config (Config):
            model (Model): 
            cycles [Cycles]:
    """

    id = db.Column(db.String(64), primary_key=True)

    def __str__(self):
        return f"<FederatedLearningProcess id : {self.id}>"


class GridNodes(db.Model):
    """ Grid Nodes table that represents connected grid nodes.
    
        Columns:
            id (primary_key) : node id, used to recover stored grid nodes (UNIQUE).
            address: Address of grid node.
    """

    __tablename__ = "__gridnode__"

    id = db.Column(db.String(64), primary_key=True)
    address = db.Column(db.String(64))

    def __str__(self):
        return f"< Grid Node {self.id} : {self.address}>"
