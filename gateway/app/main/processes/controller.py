from .federated_learning_process import FLProcess
from .federated_learning_cycle import FederatedLearningCycle


class FLPController:
    """ This class implements controller design pattern over the federated learning processes. """

    def __init__(self):
        self.processes = {}
        self._cycles = {}

    def create_cycle(
        self, model_id: str, fl_process: "FLProcess", cycle_time: int = 2500
    ):
        """ Create a new federated learning cycle.
            
            Args:
                fl_process: Federated Learning Process Structure.
                cycle_time: Remaining time to finish this cycle.
            Returns:
                fd_cycle: Cycle Instance.
        """

        cycle = FederatedLearningCycle(fl_process, cycle_time)

        # Check if Cycle already exists
        if model_id not in self._cycles:
            self._cycles[model_id] = cycle

        return cycle

    def get_cycle(self, model_id: str):
        """ Retrieve a registered cycle.
            Args:
                model_id: Model's ID.
            Returns:
                cycle: Cycle Instance / None
        """
        return self._cycles.get(model_id, None)

    def delete_cycle(self, model_id: str):
        """ Delete a registered Cycle.
            Args:
                model_id: Model's ID.
        """
        if model_id in self._cycles:
            del self._cycles[model_id]

    def create_process(
        self,
        model,
        client_plans,
        client_config,
        server_config,
        server_averaging_plan,
        client_protocols=None,
    ):
        """ Register a new federated learning process
            
            Args:
                model: The model that will be hosted.
                client_plans : an object containing syft plans.
                client_protocols : an object containing syft protocols.
                client_config: the client configurations
                server_averaging_plan: a function that will instruct PyGrid on how to average model diffs that are returned from the workers.
                server_config: the server configurations
            Returns:
                process : FLProcess Instance.
        """
        process = FLProcess(
            model=model,
            client_plans=client_plans,
            client_config=client_config,
            server_config=server_config,
            client_protocols=client_protocols,
            server_averaging_plan=server_averaging_plan,
        )

        self.processes[process.id] = process
        return self.processes[process.id]

    def delete_process(self, pid):
        """ Remove a registered federated learning process.

            Args:
                pid : Id used identify the desired process. 
        """
        del self.processes[pid]

    def get_process(self, pid):
        """ Retrieve the desired federated learning process.
            
            Args:
                pid : Id used to identify the desired process.
            Returns:
                process : FLProcess Instance or None if it wasn't found.
        """
        return self.processes.get(pid, None)
