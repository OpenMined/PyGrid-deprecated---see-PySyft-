import os.path
from . import BASE_DIR, BASE_FOLDER, AUTH_MODELS
from . import auth_credentials
from . import UserAuthentication
import getpass
import json


def create_standard_auth(path):
    # Create a new credential
    username = input("Username: ")
    password = getpass.getpass("Password:")
    credentials = json.dumps({"username": username, "password": password})

    # Save at BASE_DIR/BASE_FOLDER/UserAuthentication.FILENAME (JSON format)
    file_path = os.path.join(path, UserAuthentication.FILENAME)
    auth_file = open(file_path, "w")
    auth_file.write(credentials)
    auth_file.close()

    return UserAuthentication(username, password)


def read_authentication_configs(directory=None, folder=None):
    dir_path = directory if directory else BASE_DIR
    folder_name = folder if folder else BASE_FOLDER

    path = os.path.join(dir_path, folder_name)

    # IF directory aready exists.
    if os.path.isdir(path):
        # Check / parse every credential files.
        # Initialize authentication objects.
        # Save Objects at auth_credentials list
        for model in AUTH_MODELS:
            auth_credentials.extend(model.parse(path))
    else:
        # Create Base DIR
        os.mkdir(path)

    # If auth_credentials is empty
    if not len(auth_credentials):
        # Create new one
        auth_credentials.append(create_standard_auth(path))
    return auth_credentials
