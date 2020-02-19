import uuid
import hashlib
from .federated_learning_process import FLProcess


class FederatedLearningCycle:
    """ An abstraction of a federated learning process cycle """

    def __init__(self, fl_process: "FLProcess", model_id: str, cycle_time: int = 2500):
        """ Create a federated learning cycle instance.
            Args:
                fl_process: Federated Learning Process.
                cycle_time: Remaining time to execute this cycle.
        """
        self.fl_process = fl_process
        self.cycle_time = cycle_time
        self._hash = None

    @property
    def hash(self) -> str:
        """ Generate  and store hash code as a form of "authenticating" the download requests.
            *** This is specific to the relationship between the worker AND the cycle
            and cannot be reused for future cycles or other workers.***
            Args:
                worker_id: Worker's ID.
            Returns:
                hash_code: SHA256 code in string format.
        """
        if not self._hash:
            self._hash = self._generate_hash_key(uuid.uuid4())

        return self._hash

    def _generate_hash_key(self, primary_key: str) -> str:
        """ Generate SHA256 Hash to indentify this Cycle.
            Args:
                primary_key : Used to generate hash code.
            Returns:
                hash_code : Hash in string format.
        """
        return hashlib.sha256(bytes(primary_key)).hexdigest()
