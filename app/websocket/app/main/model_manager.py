import syft as sy

import pickle
import os

from .persistence.models import db, MLModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


model_cache = dict()


def clear_cache():
    """Clears the cache.

    """
    model_cache = dict()


def is_model_in_cache(model_id: str):
    """Checks if the given model_id is present in cache.
    
    Args:
        model_id (str): Unique id representing the model. 

    Returns:
        True is present, else False.

    """

    return model_id in model_cache


def get_model_from_cache(model_id: str):
    """Checks the cache for a model. If model not found, returns None.
    
    Args:
        model_id (str): Unique id representing the model. 

    Returns:
        An encoded model, else returns None.

    """

    return model_cache.get(model_id)


def save_model_to_cache(serialized_model: bytes, model_id: str):
    """Saves the model to cache. Will fail if a model with same id already exists.

    Args:
        serialized_model (bytes): The model object to be saved.
        model_id (str): The unique identifier associated with the model.

    """
    if is_model_in_cache(model_id):
        return
    else:
        model_cache[model_id] = serialized_model


def remove_model_from_cache(model_id: str):
    """Deletes the given model_id from cache.
    
    Args:
        model_id (str): Unique id representing the model. 

    """
    if is_model_in_cache(model_id):
        del model_cache[model_id]


def list_models():
    """Returns a list of currently existing models. Will always fetch from db.

    Returns:
        A dict with structure: {"success": Bool, "models":[model list]}.
        On error returns dict: {"success": Bool, "error": error message}. 

    """
    print(model_cache.keys())
    try:
        result = db.session.query(MLModel.id).all()
        model_ids = [model.id for model in result]
        return {"success": True, "models": model_ids}
    except SQLAlchemyError as e:
        return {"success": False, "error": str(e)}


def save_model(serialized_model: bytes, model_id: str):
    """Saves the model for later usage. 

    Args:
        serialized_model (bytes): The model object to be saved.
        model_id (str): The unique identifier associated with the model.

    Returns:
        A dict with structure: {"success": Bool, "message": "Model Saved: {model_id}"}.
        On error returns dict: {"success": Bool, "error": error message}. 

    """
    if is_model_in_cache(model_id):
        # Model already exists
        return {"success": False, "error": "Model Exists"}
    try:
        db.session.remove()
        result = db.session.add(MLModel(id=model_id, model=serialized_model))
        db.session.commit()
        # also save a copy in cache
        save_model_to_cache(serialized_model, model_id)
        return {"success": True, "message": "Model Saved: " + model_id}
    except (SQLAlchemyError, IntegrityError) as e:
        if type(e) is IntegrityError:
            # The model is already present within the db.
            # But missing from cache. Fetch the model and save to cache.
            db_model = get_model_with_id(model_id)
            if db_model != None:
                # to handle any db errors while fetching
                save_model_to_cache(db_model, model_id)
            return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": str(e)}


def get_model_with_id(model_id: str):
    """Returns a model with given model id.

    Args:
        model_id (str): The unique identifier associated with the model.

    Returns:
        A dict with structure: {"success": Bool, "model": serialized model object}.
        On error returns dict: {"success": Bool, "error": error message }. 

    """
    # load model from db.
    if is_model_in_cache(model_id):
        # Model already exists
        return {"success": True, "model": get_model_from_cache(model_id)}
    try:
        db.session.remove()
        result = db.session.query(MLModel).get(model_id)

        if result:
            # save model to cache
            save_model_to_cache(result.model, model_id)
            return {"success": True, "model": result.model}
        else:
            return {"success": False, "error": "Model not found"}
    except SQLAlchemyError as e:
        return {"success": False, "error": str(e)}


def delete_model(model_id: str):
    """Deletes the given model id. If it is present.

    Args:
        model_id (str): The unique identifier associated with the model.

    Returns:
        A dict with structure: {"success": Bool, "message": "Model Deleted: {model_id}"}.
        On error returns dict: {"success": Bool, "error": {error message}}. 

    """

    try:
        # first del from cache
        remove_model_from_cache(model_id)
        # then del from db
        result = db.session.query(MLModel).get(model_id)
        db.session.delete(result)
        db.session.commit()
        return {"success": True, "message": "Model Deleted: " + model_id}
    except SQLAlchemyError as e:
        # probably no model found in db.
        return {"success": False, "error": str(e)}


def check_if_model_exists(model_id: str):
    """Checks whether the given model_id is saved or not.

    Args:
        model_id (str): The unique identifier associated with the model.

    Returns:
        True if model is present, else false.

    """

    try:
        result = db.session.query(MLModel).get(model_id)
        return True
    except SQLAlchemyError as e:
        # probably no model found with the model_id specified
        return False
