from typing import List

from .database import db_instance
from .model_cache import ModelCache
from ..codes import MODEL
from syft.serde import serialize, deserialize
import hashlib


class ModelStorage:
    def __init__(self, worker):
        self.worker = worker
        self.cache = ModelCache()

    @property
    def id(self):
        return self.worker.id

    @property
    def models(self) -> List:
        if db_instance():
            key = self._generate_hash_key()
            size = db_instance().llen(key)
            model_ids = db_instance().lrange(key, 0, size)
            model_ids = [id.decode("utf-8") for id in model_ids]
            return model_ids

        return self.cache.models

    def save_model(
        self,
        serialized_model: bytes,
        model_id: str,
        allow_download: bool,
        allow_remote_inference: bool,
        mpc: bool,
    ) -> bool:

        if db_instance():
            key = self._generate_hash_key(model_id)
            model = {
                MODEL.MODEL: serialized_model,
                MODEL.ALLOW_DOWNLOAD: int(allow_download),
                MODEL.ALLOW_REMOTE_INFERENCE: int(allow_remote_inference),
                MODEL.MPC: int(mpc),
            }

            # Save serialized model into db
            # Format: { hash(worker_id + model_id) : dict( serialized_model, allow_download, allow_inference, mpc) }
            result = db_instance().hmset(key, model)

            primary_key = self._generate_hash_key()

            # Save model id
            db_instance().lpush(primary_key, model_id)

        self.cache.save(
            serialized_model,
            model_id,
            allow_download,
            allow_remote_inference,
            mpc,
            serialized=True,
        )

    def get(self, model_id: str):
        if self.cache.contains(model_id):
            return self.cache.get(model_id)

        if db_instance():
            key = self._generate_hash_key(model_id)
            raw_data = db_instance().hgetall(key)

            # Decode binary keys
            raw_data = {key.decode("utf-8"): value for key, value in raw_data.items()}

            # Decode binary values
            raw_data[MODEL.ALLOW_DOWNLOAD] = bool(
                int(raw_data[MODEL.ALLOW_DOWNLOAD].decode("utf-8"))
            )
            raw_data[MODEL.ALLOW_REMOTE_INFERENCE] = bool(
                int(raw_data[MODEL.ALLOW_REMOTE_INFERENCE].decode("utf-8"))
            )
            raw_data[MODEL.MPC] = bool(int(raw_data[MODEL.MPC].decode("utf-8")))

            # Save model in cache
            self.cache.save(
                raw_data[MODEL.MODEL],
                model_id,
                raw_data[MODEL.ALLOW_DOWNLOAD],
                raw_data[MODEL.ALLOW_REMOTE_INFERENCE],
                raw_data[MODEL.MPC],
                True,
            )

            return self.cache.get(model_id)
        else:
            return None

    def remove(self, model_id) -> bool:
        # Remove model from cache
        self.cache.remove(model_id)

        if db_instance():
            # Remove model ID from id's list
            ids_list_key = self._generate_hash_key()
            db_instance().lrem(ids_list_key, 0, model_id)

            # Remove model from database
            key = self._generate_hash_key(model_id)
            return db_instance().delete(key)
        else:
            return True

    def contains(self, model_id):
        key = self._generate_hash_key(model_id)
        if not db_instance():
            return self.cache.contains(model_id)
        else:
            return self.cache.contains(model_id) or bool(db_instance().hgetall(key))

    def _generate_hash_key(self, primary_key: str = "") -> str:
        return hashlib.sha256(bytes(self.id + primary_key, "utf-8")).hexdigest()
