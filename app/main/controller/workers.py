from ..models.warehouse import Warehouse
from ..models.worker import Worker


class Workers:
    def __init__(self):
        self.__workers = Warehouse(Worker)

    def is_eligible(self, worker_id: str, server: dict):
        """ Check if Worker is eligible to join in an new cycle by using its bandwith statistics.
            Args:
                worker_id : Worker's ID.
                server_confing : FL Process Server Config.
            Returns:
                result: Boolean flag.
        """
        _worker = self.__workers.first(worker_id=worker_id)

        # Check bandwith
        _comp_bandwith = (
            _worker.avg_upload > server.config["minimum_upload_speed"]
        ) and (_worker.avg_download > server.config["minimum_download_speed"])

        return _comp_bandwith
