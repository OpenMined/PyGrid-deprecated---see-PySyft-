from typing import Union

from . import get_db_instance

from syft.serde import serialize, deserialize
from syft.generic.frameworks.types import FrameworkTensorType
from syft.generic.tensor import AbstractTensor
from syft.generic.object_storage import ObjectStorage


def set_persistent_mode(redis_db):
    ''' Update/ Overwrite PySyft ObjectStorage to work in a persistent mode.'''
    def _set_obj(self, obj: Union[FrameworkTensorType, AbstractTensor]) -> None:
        """Adds an object to the registry of objects.
        Args:
            obj: A torch or syft tensor with an id.
        """
        self._objects[obj.id] = obj
        redis_db.hset(self.id, obj.id, serialize(obj))

    def _rm_obj(self, remote_key: Union[str, int]):
        """Removes an object.
        Remove the object from the permanent object registry if it exists.
        Args:
            remote_key: A string or integer representing id of the object to be
            removed.
        """
        if remote_key in self._objects:
            del self._objects[remote_key]
        redis_db.hdel(self.id, obj.id)

    def _force_rm_obj(self, remote_key: Union[str, int]):
        """Forces object removal.
        Besides removing the object from the permanent object registry if it exists.
        Explicitly forces removal of the object modifying the `garbage_collect_data` attribute.
        Args:
            remote_key: A string or integer representing id of the object to be
            removed.
        """
        if remote_key in self._objects:
            obj = self._objects[remote_key]
            if hasattr(obj, "child") and hasattr(obj.child, "garbage_collect_data"):
                obj.child.garbage_collect_data = True
            del self._objects[remote_key]
        redis_db.hdel(self.id, remote_key)

    def _get_obj(self, obj_id: Union[str, int]) -> object:
        """Returns the object from registry.
        Look up an object from the registry using its ID.
        Args:
            obj_id: A string or integer id of an object to look up.
        Returns:
            Object with id equals to `obj_id`.
        """
        try:
            obj = self._objects[obj_id]
        except KeyError as e:
            if obj_id not in self._objects:
                # Try to recover object on database
                obj = redis_db.hget(self.id, obj_id)
                if obj:
                    self._objects[obj_id] = deserialize(obj)
                else:
                    raise ObjectNotFoundError(obj_id, self)
            else:
                raise e
        return obj

    # Overwrite default object storage methods
    ObjectStorage.set_obj = _set_obj
    ObjectStorage.get_obj = _get_obj
    ObjectStorage.rm_obj = _rm_obj
    ObjectStorage.force_rm_obj = _force_rm_obj

def recover_objects( worker ):
    raw_objs = get_db_instance().hgetall(worker.id)
    objects = { int(key.decode('utf-8')) : deserialize(value) for key, value in raw_objs.items() }
    worker._objects = objects
    return worker
