from .database import db_instance
from .model_cache import ModelCache
from syft.serde import serialize, deserialize
import hashlib


class ModelStorage:
    def __init__(self, worker):
        self.worker = worker
        self.cache = ModelCache()

    @property
    def id(self):
        return self.worker.id

    def save_model(
        self,
        serialized_model: bytes,
        model_id: str,
        allow_download: bool,
        allow_remote_inference: bool,
        mpc: bool,
    ) -> bool:

        key = self._generate_hash_key(model_id)
        model = {
            "id": model_id,
            "model": serialized_model,
            "allow_download": int(allow_download),
            "allow_inference": int(allow_remote_inference),
            "mpc": int(mpc),
        }

        result = db_instance().hmset(key, model)

        self.cache.save(
            serialized_model,
            model_id,
            allow_download,
            allow_remote_inference,
            mpc,
            serialized=True,
        )

    def save_states(self, model) -> bool:
        states = {id: serialize(self.worker.get(id)) for id in model.state_ids}

        key = self._generate_hash_key(model.id)
        return db_instance().hmset(key, states)

    def get_states(self, model):
        raw_states = self.get(model.id)
        states = {
            int(key.decode("utf-8")): deserialize(value)
            for key, value in raw_states.items()
        }
        self.worker._objects = {**self.worker._objects, **states}

    def get(self, model_id: str):
        key = self._generate_hash_key(model_id)
        raw_data = db_instance().hgetall(key)
        raw_data = {key.decode("utf-8"): value for key, value in raw_data.items()}
        return raw_data

    def get_all(self):
        return db_instance().hgetall(self.id)

    def remove(self, model_id) -> bool:
        self.cache.remove(model_id)
        key = self._generate_hash_key(model_id)
        return db_instance().delete(key)

    def _generate_hash_key(self, model_id: str) -> str:
        return hashlib.sha256(bytes(self.id + model_id, "utf-8")).hexdigest()
