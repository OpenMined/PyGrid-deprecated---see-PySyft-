import uuid
import hashlib
from .federated_learning_process import FLProcess


class FederatedLearningCycle:
    """ An abstraction of a federated learning process cycle """

    def __init__(self, fl_process: "FLProcess", cycle_time: int = 2500):
        """ Create a federated learning cycle instance.
            Args:
                fl_process: Federated Learning Process.
                cycle_time: Remaining time to execute this cycle.
        """
        self.fl_process = fl_process
        self._workers = []
        self.cycle_time = cycle_time
        self._hash_keys = {}

    def insert(self, worker_id: str) -> bool:
        """ Insert a new worker into this Federated Learning Cycle.
            If worker_id already exists in this cycle returns false, otherwise return True.
            
            Args:
                worker_id: Worker's ID.
            Returns:
                result : boolean flag
        """
        # Check if worker id already exists
        if worker_id in self.workers:
            return False
        else:
            self.workers.append(worker_id)
            return True

    def new_hash(self, worker_id: str) -> str:
        """ Generate  and store hash codes as a form of "authenticating" the download requests.
            
            *** This is specific to the relationship between the worker AND the cycle
            and cannot be reused for future cycles or other workers.***
            
            Args:
                worker_id: Worker's ID.
            Returns:
                hash_code: SHA256 code in string format.
        """
        hash_code = self._generate_hash_key(uuid.uuid4())
        self.hash_keys[worker_id] = hash_code
        return hash_code

    def validate(self, worker_id: str, hash_code: str) -> bool:
        """ Validate workers by hash codes.
            Args:
                worker_id: Worker's ID.
                hash_code: Hash to be checked.
            Returns:
                result : boolean flag
        """
        return self.hash_keys[worker_id] == hash_code

    def _generate_hash_key(self, primary_key: str) -> str:
        """ Generate SHA256 Hash to indentify this Cycle.
            Args:
                primary_key : Used to generate hash code.
            Returns:
                hash_code : Hash in string format.
        """
        return hashlib.sha256(bytes(primary_key)).hexdigest()
