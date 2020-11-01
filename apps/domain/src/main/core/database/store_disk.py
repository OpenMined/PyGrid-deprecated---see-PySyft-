from . import db, BaseModel

from syft.core.store import ObjectStore


class DiskObjectStore(ObjectStore):
    def __init__(self, db):
        self.db = db

    def store(self, obj: BaseModel) -> None:
        self.db.session.add(obj)
        self.db.session.commit()

    def __contains__(self, obj: BaseModel) -> None:
        self.db.session.rollback()

        contains = False
        if obj.id is not None:
            contains = self.db.session.query(type(obj)).get(obj.id) is not None

        return contains

    def __setitem__(self, _id: int, data_type: BaseModel, new_fields: dict) -> None:
        obj = self.db.session.query(data_type).get(_id)
        for key, value in new_fields.items():
            setattr(obj, key, value)

        self.db.session.commit()

    def __delitem__(self, _id: int, data_type: BaseModel) -> None:
        obj = self.db.session.query(data_type).get(_id)

        self.db.session.delete(obj)
        self.db.session.commit()
