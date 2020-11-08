from typing import List

from torch import Tensor
from syft.core.store import ObjectStore
from syft.core.common.uid import UID
from syft.core.common.serde import _deserialize
from syft.core.store.storeable_object import StorableObject

from .bin_storage.bin_obj import BinaryObject
from .bin_storage.metadata import StorageMetadata, get_metadata
from . import db, BaseModel

ENCODING = "UTF-8"


# from main.core.database.bin_storage.metadata import *
def create_storable(
    _id: UID, data: Tensor, description: str, tags: List[str]
) -> StorableObject:
    obj = StorableObject(id=_id, data=data, description=description, tags=tags)

    return obj


class DiskObjectStore(ObjectStore):
    def __init__(self, db):
        self.db = db

    def store(self, obj: StorableObject) -> None:
        bin_obj = BinaryObject(id=obj.id.value.hex, binary=obj.to_bytes())
        metadata = get_metadata(self.db)
        metadata.length += 1

        self.db.session.add(bin_obj)
        self.db.session.commit()

    def __contains__(self, item: UID) -> bool:
        self.db.session.rollback()
        _id = item.value.hex
        return self.db.session.query(BinaryObject).get(_id) is not None

    def __setitem__(self, key: UID, value: StorableObject) -> None:
        obj = self.db.session.query(BinaryObject).get(key.value.hex)
        obj.binary = value.to_bytes()
        self.db.session.commit()

    def __delitem__(self, key: UID) -> None:
        obj = self.db.session.query(BinaryObject).get(key.value.hex)
        metadata = get_metadata(self.db)
        metadata.length -= 1

        self.db.session.delete(obj)
        self.db.session.commit()

    def __len__(self) -> int:
        return get_metadata(self.db).length

    def keys(self) -> List[UID]:
        ids = self.db.session.query(BinaryObject.id).all()
        return [UID.from_string(value=_id[0]) for _id in ids]

    def clear(self) -> None:
        self.db.session.query(BinaryObject).delete()
        self.db.session.query(StorageMetadata).delete()
        self.db.session.commit()

    def values(self) -> List[StorableObject]:
        # TODO _deserialize creates storable with no data or tags
        binaries = self.db.session.query(BinaryObject.binary).all()
        binaries = [_deserialize(blob=b[0], from_bytes=True) for b in binaries]
        return binaries

    def __str__(self) -> str:
        objs = self.db.session.query(BinaryObject).all()
        objs = [obj.__str__() for obj in objs]
        return "{}\n{}".format(get_metadata(self.db).__str__(), objs)
