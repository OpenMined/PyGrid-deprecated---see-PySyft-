from syft import Plan
from syft.serde import deserialize
from .model_storage import ModelStorage


class ModelController:

    # Error Messages
    ID_CONFLICT_MSG = "Model id already exists."
    MODEL_NOT_FOUND_MSG = "Model not found."
    MODEL_DELETED_MSG = "Model deleted with success!"

    def __init__(self):
        self.model_storages = dict()

    def save(
        self,
        worker,
        serialized_model: bytes,
        model_id: str,
        allow_download: bool,
        allow_remote_inference: bool,
        mpc: bool,
    ):
        storage = self.get_storage(worker)

        if storage.cache.contains(model_id):
            return {"success": False, "error": ModelController.ID_CONFLICT}

        # Saves a copy in the database
        storage.save_model(
            serialized_model, model_id, allow_download, allow_remote_inference, mpc
        )

        model = deserialize(serialized_model)

        return {"success": True, "message": "Model saved with id: " + model_id}

    def get(self, worker, model_id: str):
        storage = self.get_storage(worker)

        if storage.cache.contains(model_id):
            return {"success": True, "model": storage.cache.get(model_id)}

        raw_model = storage.get(model_id)
        model = deserialize(raw_model["model"])

        if model:
            storage.cache.save(
                model,
                model_id,
                raw_model["allow_download"],
                raw_model["allow_inference"],
                raw_model["mpc"],
                False,
            )
            return {"success": True, "model": storage.cache.get(model_id)}
        else:
            return {"success": False, "error": ModelController.MODEL_NOT_FOUND_MSG}

    def delete(self, worker, model_id: str):
        storage = self.get_storage(worker)

        # Build response
        response = {}
        response["success"] = bool(storage.remove(model_id))

        # set log messages
        if response["success"]:
            response["message"] = "Model deleted with success!"
        else:
            response["error"] = "Model id not found on database!"

        return response

    def get_storage(self, worker):
        if worker.id in self.model_storages:
            storage = self.model_storages[worker.id]
        else:
            storage = self._new_storage(worker)
        return storage

    def _new_storage(self, worker):
        new_storage = ModelStorage(worker)
        self.model_storages[worker.id] = new_storage
        return new_storage
