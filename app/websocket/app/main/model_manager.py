import syft as sy

import pickle
import os


def models_list():
    """Returns a list of currently excisting models

    Returns:
        A list object, containig model_id of all the models.

    """

    files = os.listdir(os.curdir + "/models/")  # files and directories
    # removing the .pickle file extension
    files = [f.replace(".pickle", "") for f in files]
    return files


def save_model_for_serving(serialized_model: bytes, model_id: str):
    """Saves the model for later usage. 

    Args:
        serialized_model (bytes): The model object to be saved. encoded in ("ISO-8859-1")
        model_id (str): The unique identifier associated with the model

    Returns:
        True for success, False otherwise.

    """

    # check if model already exists. If yes then return false
    if check_if_model_exists(model_id):
        return False

    # saving the model to a file. Will only work if server has write access
    with open("models/" + model_id + ".pickle", "wb") as handle:
        try:
            pickle.dump(serialized_model, handle)
        except Exception as e:
            print("Exception in save_model_for_serving {}".format(e))
            return False

    return True


def get_model_with_id(model_id: str):
    """Returns a model with model id

    Args:
        model_id (str): The unique identifier associated with the model

    Returns:
        A model object, if found, else returns none

    """
    # load the file using pickle
    try:
        with open("models/" + model_id + ".pickle", "rb") as f:
            try:
                model = pickle.load(f)
                return model
            except:
                return None
    except Exception as e:
        print("Exception in get_model_with_id {}".format(e))
        return None

    return None


def delete_model(model_id: str):
    """Deletes the given model id. If it is present.

    Args:
        model_id (str): The unique identifier associated with the model

    Returns:
        True is model was deleted successfully

    """

    if check_if_model_exists(model_id):
        os.remove("models/" + model_id + ".pickle")
        return True
    else:
        return False


def check_if_model_exists(model_id):
    """Checks whether the given model_id is saved or not.

    Args:
        model_id (str): The unique identifier associated with the model

    Returns:
        True if model is present, else false

    """

    models = models_list()
    if any(model_id == f for f in models):
        return True
    else:
        return False
