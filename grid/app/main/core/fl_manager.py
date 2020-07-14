import abc

from syft import Plan

from ..sfl.processes import \
    ProcessManager  # TODO: Should we move ProcessManager to core submodule?


class FLManager(metaclass=abc.ABCMeta):
    """Abstract Federated Learning Manager for both Static and Dynamic
    Federated Learning."""

    def __init__(self, fl_type: str) -> None:
        """Initialization of the class.

        Args:
            fl_type (str): Type of the Federated Learning Process
        """
        super().__init__()
        self._fl_type = fl_type

    @abc.abstractmethod
    def _generate_hash_key(self, primary_key: str) -> str:
        # TODO: implement this one
        pass

    @abc.abstractmethod
    def create_process(
        self,
        model: object,  # TODO: need to update the type Union[tf, torch]
        client_plans: Plan,  # TODO: need to update the type syft.plan
        client_config: dict,
        server_config: dict,
        server_averaging_plan: Plan,  # TODO: need to update the type from syft
        client_protocols: object = None,  # TODO: need to update the type from syft
    ) -> ProcessManager:
        pass

    @abc.abstractmethod
    def last_cycle(self, worker_id: str, name: str, version: str,) -> int:
        pass

    @abc.abstractmethod
    def assign(
        self,
        name: str,
        version: str,
        worker: object,  # TODO: need to be updated
        last_participation: int,
    ) -> int:
        pass

    @abc.abstractmethod
    def submit_diff(self, worker_id: str, request_key: str, diff: bin):
        pass
