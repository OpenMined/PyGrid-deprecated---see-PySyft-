import syft as sy

import pickle
import os

from .persistence.models import db, SyftModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


model_cache = dict()

def cache_get_model(model_id: str):
    """Checks the cache for a model. If model not found, returns None.
    
    Args:
        model_id (str): Unique id representing the model. 

    Returns:
        A model encoded in ("ISO-8859-1"), else returns None.

    """
    model_ids = model_cache.keys()
    if model_id in model_ids:
        # model found
        return model_cache[model_id]

    return None

def cache_save_model(serialized_model: bytes, model_id: str):
    """Saves the model to cache. Will fail if a model with same id already exists.

    Args:
        serialized_model (bytes): The model object to be saved. encoded in ("ISO-8859-1").
        model_id (str): The unique identifier associated with the model.

    Returns:
        True for success, False otherwise.

    """
    if cache_get_model(model_id) is None:
        model_cache[model_id] = serialized_model
        return True
    else:
        return False

def cache_del_model(model_id: str):
    """Deletes the given model_id. If it fails (model not present) it returns False.
    
    Args:
        model_id (str): Unique id representing the model. 

    Returns:
        True is deleted, false otherwise.

    """
    if cache_get_model(model_id) is None:
        return False
    else:
        del model_cache[model_id]


def models_list():
    """Returns a list of currently existing models. Will always fetch from db.

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
    if cache_get_model(model_id) != None:
        # Model already exists
        return False
    try:
        db.session.remove()
        result = db.session.add(SyftModel(id=model_id, model=serialized_model))
        db.session.commit()
        # also save a copy in cache
        cache_save_model(serialized_model, model_id)
        return True
    except (SQLAlchemyError, IntegrityError) as e:
        if type(e) is IntegrityError:
            # The model is already present within the db.
            # But missing from cache. Fetch the model and save to cache.
            db_model = get_model_with_id(model_id)
            if db_model != None:
                # to handle any db errors while fetching
                cache_save_model(db_model, model_id)
            return False
        else:
            # Some other error occured within db
            return False


def get_model_with_id(model_id: str):
    """Returns a model with model id.

    Args:
        model_id (str): The unique identifier associated with the model.

    Returns:
        A model object, if found, else returns none.

    """
    # load model from db.
    if cache_get_model(model_id) != None:
        # Model already exists
        return cache_get_model(model_id)
    try:
        db.session.remove()
        result = db.session.query(SyftModel).get(model_id)
        
        if result is None:
            # no model found
            return None

        # save model to cache
        cache_save_model(result.model, model_id)
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
        # first del from cache
        cache_del_model(model_id)
        # then del from db
        result = db.session.query(SyftModel).get(model_id)
        db.session.delete(result)
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        # probably no model found in db.
        return False


def check_if_model_exists(model_id: str):
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
