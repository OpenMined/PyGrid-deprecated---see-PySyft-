class User:
    """ An abstraction of a user. """

    def __init__(self, username: str, password: str):
        """ Create a user instance.
            
            Args:
                username: the name that uniquely identifies the user.
                password : the user's password.
        """
        self._username = username
        self._password = password
        self._fl_processes = dict()

    def register_fl_process(self, pid: str, process):
        """ Register a new Federated Learning Process upload by this user.
            Args:
                pid (str): Process ID used to identify the new federated learning process.
                process (FederatedLearningProcess): FederatedLearningProcess instance to be registered.
        """
        self._fl_processes[pid] = process

    def get_fl_process(self, pid: str):
        """ Retrieves a Federated Learning Process that belongs to this user.
            Args:
                pid (str): Process ID used to identify the new federated learning process.
            Returns:
                process (FederatedLearningProcess): a FederatedLearningProcess instance identified by that pid.
        """
        return self._fl_processes.get(pid)

    def unregister_fl_process(self, pid):
        """ Unregister a Federated Learning Process that belongs to this user.
            Args:
                pid (str): Process ID used to identify the new federated learning process.
        """
        del self._fl_processes[pid]
        
    @property
    def username(self) -> str:
        """ Get username of this username.
            Returns:
                username (str) : session's username.
        """
        return self._username
