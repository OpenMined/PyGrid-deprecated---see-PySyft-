import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Model(db.Model):
    """ Model table that represents the AI Models.
        Columns:
            id (String, primary_key) : Model's id, used to recover stored model.
            version (String) : Model version.
            checkpoints (list) : Model Checkpoints.
    """

    __tablename__ = "__model__"

    id = db.Column(db.String(), primary_key=True)
    version = db.Column(db.String())
    # TODO:
    # checkpoints = list(ModelCheckpoints)

    def __str__(self):
        return f"<Model  id: {self.id}, version: {self.version}>"


class ModelCheckPoint(db.Model):
    """ Model's save points.
        Columns:
            id (String, primary_key): Checkpoint ID.
            values (Binary): Value of the model at a given checkpoint.
    """

    __tablename__ = "__model_checkpoint__"

    id = db.Column(db.String(), primary_key=True)
    values = db.Column(db.LargeBinary)
    """
    @property
    def object(self):
        return sy.serde.deserialize(self.values)

    @object.setter
    def object(self):
        self.data = sy.serde.serialize(self.values)
    """

    def __str__(self):
        return f"<CheckPoint id: {self.id} , values: {self.data}>"


class Plan(db.Model):
    """ Plan table that represents Syft Plans.
        Columns:
            id (String): Plan ID.
            value (String): String  (List of operations)
            value_ts (String): String (TorchScript)
    """

    __tablename__ = "__plan__"

    id = db.Column(db.String(), primary_key=True)
    value = db.Column(db.String())
    value_ts = db.Column(db.String())

    def __str__(self):
        return (
            f"<Plan id: {self.id}, values: {self.value}, torchscript: {self.value_ts}>"
        )


class Protocol(db.Model):
    """ Protocol table that represents Syft Protocols.
        Columns:
            id (String, Primary Key): Protocol ID.
            value: String  (List of operations)
            value_ts: String (TorchScript)
    """

    __tablename__ = "__protocol__"

    id = db.Column(db.String(), primary_key=True)
    value = db.Column(db.String())
    value_ts = db.Column(db.String())

    def __str__(self):
        return f"<Protocol id: {self.id}, values: {self.value}, torchscript: {self.value_ts}>"


class Config(db.Model):
    """ Configs table.
        Columns:
            id (String, Primary Key): Config ID.
            value (String): Dictionary
    """

    __tablename__ = "__config__"

    id = db.Column(db.String(), primary_key=True)
    config = db.Column(db.String())

    @property
    def object(self):
        # Convert Python Dict data structure to String
        return json.dumps(self.config)

    @object.setter
    def object(self):
        # Convert Python String to Dict data tructure
        self.config = json.loads(self.config)

    def __str__(self):
        return f"<Config id: {self.id} , configs: {self.config}>"


class Cycle(db.Model):
    """ Cycle table.
        Columns:
            id (String):
            start (TIME): Start time.
            end (TIME): End time.
            worker_cycles:
    """

    __tablename__ = "__cycle__"

    id = db.Column(db.String(), primary_key=True)
    start = db.Column(db.DateTime())
    end = db.Column(db.DateTime())
    sequence = db.Column(db.BigInteger())
    # TODO:
    # worker_cycles =

    def __str__(self):
        return f"< Cycle id : {self.id}, start: {self.start}, end: {self.end}>"


class WorkerCycle(db.Model):
    """ Relation between Workers and Cycles.
        Columns:
            id (String):
            fl_process_id (String):
            cycle_id (String):
            worker_id (String):
            request_key (String): unique token that permits downloading specific Plans, Protocols, etc.
    """

    __tablename__ = "__worker_cycle__"

    id = db.Column(db.String(), primary_key=True)
    fl_process_id = db.Column(db.String())
    cycle_id = db.Column(db.String())
    worker_id = db.Column(db.String())
    request_key = db.Column(db.String())

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

    __tablename__ = "__worker__"

    id = db.Column(db.String(), primary_key=True)
    format_preference = db.Column(db.String())
    ping = db.Column(db.BigInteger)
    avg_download = db.Column(db.BigInteger)
    avg_upload = db.Column(db.BigInteger)
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
            client_config (Config):
            protocols (Protocol) :
            server_config (Config):
            model (Model): 
            cycles [Cycles]:
    """

    __tablename__ = "__fl_process__"

    id = db.Column(db.String(), primary_key=True)

    def __str__(self):
        return f"<FederatedLearningProcess id : {self.id}>"


class GridNodes(db.Model):
    """ Grid Nodes table that represents connected grid nodes.
    
        Columns:
            id (primary_key) : node id, used to recover stored grid nodes (UNIQUE).
            address: Address of grid node.
    """

    __tablename__ = "__gridnode__"

    id = db.Column(db.String(), primary_key=True)
    address = db.Column(db.String())

    def __str__(self):
        return f"< Grid Node {self.id} : {self.address}>"
