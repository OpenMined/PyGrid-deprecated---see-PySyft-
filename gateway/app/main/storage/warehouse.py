from .models import db


class Warehouse:
    def __init__(self, schema):
        self._schema = schema

    def register(self, *kwargs):
        """ Register e  new object into the database.
            Args:
                parameters : List of object parameters.
        """
        new_obj = self._schema(kwargs)
        db.session.add(new_obj)
        db.session.commit()

    def query(self, *kwargs):
        """ Query db objects filtering by parameters
            Args:
                parameters : List of parameters used to filter. 
        """
        objects = self._schema.query.filter_by(kwargs)
        return objects

    def contains(self, id):
        """ Check if the object id already exists into the database.
            Args:
                id: Object ID.
        """
        return self._schema.query.filter_by(id=id) != None

    def delete(self, *kwargs):
        """ Delete an object from the database.
            Args:
                parameters: Parameters used to filter the object.
        """
        object_to_delete = self.query(kwargs)
        db.session.delete(object_to_delete)
        db.session.commit()
