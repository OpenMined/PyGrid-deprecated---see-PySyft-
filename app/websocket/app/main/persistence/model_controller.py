from syft import Plan
from syft.serde import deserialize
from syft.codes import RESPONSE_MSG
from .model_storage import ModelStorage
from ..codes import MODEL


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
        mpc: bool = False,
    ):
        storage = self.get_storage(worker)

        if storage.contains(model_id):
            return {
                RESPONSE_MSG.SUCCESS: False,
                RESPONSE_MSG.ERROR: ModelController.ID_CONFLICT_MSG,
            }

        # Saves a copy in the database
        storage.save_model(
            serialized_model, model_id, allow_download, allow_remote_inference, mpc
        )
        return {
            RESPONSE_MSG.SUCCESS: True,
            "message": "Model saved with id: " + model_id,
        }

    def get(self, worker, model_id: str):
        storage = self.get_storage(worker)
        if storage.contains(model_id):
            return {RESPONSE_MSG.SUCCESS: True, MODEL.PROPERTIES: storage.get(model_id)}
        else:
            return {
                RESPONSE_MSG.SUCCESS: False,
                RESPONSE_MSG.ERROR: ModelController.MODEL_NOT_FOUND_MSG,
            }

    def delete(self, worker, model_id: str):
        storage = self.get_storage(worker)

        # Build response
        response = {}
        response[RESPONSE_MSG.SUCCESS] = bool(storage.remove(model_id))

        # set log messages
        if response[RESPONSE_MSG.SUCCESS]:
            response["message"] = "Model deleted with success!"
        else:
            response[RESPONSE_MSG.ERROR] = "Model id not found on database!"

        return response

    def models(self, worker):
        storage = self.get_storage(worker)
        return {RESPONSE_MSG.SUCCESS: True, RESPONSE_MSG.MODELS: storage.models}

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
