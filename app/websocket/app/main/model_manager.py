import syft as sy

import pickle
import os

from .persistence.models import db, SyftModel
from sqlalchemy.exc import SQLAlchemyError


def models_list():
    """Returns a list of currently existing models.

    Returns:
        A list object, containig model_id of all the models.

    """

    try:
        result = db.session.query(SyftModel.id).all()
        model_names = []
        for model in result:
            model_names.append(model.id)
        return model_names
    except SQLAlchemyError as e:
        # probably no model found with the model_id specified
        return None


def save_model_for_serving(serialized_model: bytes, model_id: str):
    """Saves the model for later usage. 

    Args:
        serialized_model (bytes): The model object to be saved. encoded in ("ISO-8859-1").
        model_id (str): The unique identifier associated with the model.

    Returns:
        True for success, False otherwise.

    """
    try:
        result = db.session.add(SyftModel(id=model_id, model=serialized_model))
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        # if model already exists return false
        return False


def get_model_with_id(model_id: str):
    """Returns a model with model id.

    Args:
        model_id (str): The unique identifier associated with the model.

    Returns:
        A model object, if found, else returns none.

    """
    # load model from db.
    try:
        result = db.session.query(SyftModel).get(model_id)
        return result.model
    except SQLAlchemyError as e:
        # probably no model found with the model_id specified
        return None


def delete_model(model_id: str):
    """Deletes the given model id. If it is present.

    Args:
        model_id (str): The unique identifier associated with the model.

    Returns:
        True is model was deleted successfully.

    """

    try:
        result = db.session.query(SyftModel).get(model_id)
        db.session.delete(result)
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        # probably no model found with the model_id specified
        return False


def check_if_model_exists(model_id):
    """Checks whether the given model_id is saved or not.

    Args:
        model_id (str): The unique identifier associated with the model.

    Returns:
        True if model is present, else false.

    """

    try:
        result = db.session.query(SyftModel).get(model_id)
        return True
    except SQLAlchemyError as e:
        # probably no model found with the model_id specified
        return False
