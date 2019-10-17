import os.path
from . import BASE_DIR, BASE_FOLDER, AUTH_MODELS
from . import auth_credentials
from . import UserAuthentication
import getpass
import json


def register_new_credentials(path):
    """ We use this function to create a new credential if we don't find any credential during
        load_credentials function.

        Args:
            path (str) : .openmined credentials path
        Returns:
            UserAuthentication : A Instance of our new credential.
    """
    # Create a new credential
    username = input("Username: ")
    password = getpass.getpass("Password:")
    first_user = {"username": username, "password": password}
    credentials = json.dumps({"credential": [first_user]})

    # Save at BASE_DIR/BASE_FOLDER/UserAuthentication.FILENAME (JSON format)
    file_path = os.path.join(path, UserAuthentication.FILENAME)
    auth_file = open(file_path, "w")
    auth_file.write(credentials)
    auth_file.close()

    return UserAuthentication(username, password)


def read_authentication_configs(directory=None, folder=None):
    """ Search for a path and folder used to store user credentials
        
        Args:
            directory (str) : System path (can usually be /home/<user>).
            folder (str) : folder name used to store PyGrid credentials.

        Returns:
            List : List of credentials instances.
    """
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
        auth_credentials.append(register_new_credentials(path))
    return auth_credentials


def search_credential(user):
    """ Search for a specific credential instance.
        
        Args:
            user : key used to identify some credential.
        Returns:
            BaseAuthentication : Credential's instance.
    """
    for cred in auth_credentials:
        if cred.username == user:
            return cred
