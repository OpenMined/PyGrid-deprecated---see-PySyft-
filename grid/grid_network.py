import requests
import json
import syft as sy
from grid.websocket_client import WebsocketGridClient
from grid.utils import connect_all_nodes
import torch


class GridNetwork(object):
    """  The purpose of the Grid Network class is to control the entire communication flow by abstracting operational steps.
    
        Attributes:
            - gateway_url : network address to which you want to connect.
            - connected_grid_nodes : Grid nodes that are connected to the application.
    """

    def __init__(self, gateway_url):
        self.gateway_url = gateway_url

    def search(self, *query):
        """ Search a set of tags across the grid network.
            
            Arguments:
                query : A set of dataset tags.
            Returns:
                tensor_matrix : matrix of tensor pointers.
        """
        body = json.dumps({"query": list(query)})

        # Asks to grid gateway about dataset-tags
        response = requests.post(self.gateway_url + "/search", data=body)

        # List of nodes that contains the desired dataset
        match_nodes = json.loads(response.content)

        # Connect with grid nodes that contains the dataset and get their pointers
        tensor_set = []
        for node_id, node_url in match_nodes:
            worker = self.__connect_with_node(node_id, node_url)
            tensor_set.append(worker.search(*query))
        return tensor_set

    def serve_model(self, model, model_id=None, encrypted=False):
        """ This method will one/more grid node(s) to host an encrypted or decrypted model.
            Args:
                model : Model to be hosted.
                model_id : Model's ID.
                encrypted: Boolean flag to perform SMPC host.
        """
        if encrypted:
            self._serve_encrypted_model(model)
        else:
            self._serve_non_encrypted_model(model, model_id)

    def _serve_encrypted_model(self, model):
        # Model need to be a plan
        if isinstance(model, sy.Plan):
            response = requests.get(self.gateway_url + "/choose-encrypted-model-host")
            hosts = json.loads(response.content)
            if (
                len(hosts) and len(hosts) % 4 == 0
            ):  # Minimum workers chunk to share and host a model (3 to SMPC operations, 1 to host)
                smpc_initial_interval = 0
                for i in range(0, len(hosts), 4):
                    # Connect with host worker
                    host = self.__connect_with_node(*hosts[i])

                    # Connect with SMPC Workers
                    smpc_end_interval = i - 1
                    smpc_workers_info = hosts[smpc_initial_interval:smpc_end_interval]
                    smpc_workers = []
                    for worker in smpc_workers_info:
                        smpc_workers.append(self.__connect_with_node(*worker))

                    # Connect with crypto provider
                    crypto_provider = self.__connect_with_node(
                        *hosts[smpc_end_interval]
                    )

                    # # Connect nodes to each other
                    model_nodes = smpc_workers + [crypto_provider, host]
                    connect_all_nodes(model_nodes)

                    # SMPC Share
                    model.fix_precision().share(
                        *smpc_workers, crypto_provider=crypto_provider
                    )
                    # Host model
                    model.send(host)

                    for node in model_nodes:
                        node.disconnect()
                    smpc_initial_interval = i  # Initial index of next chunk
            # If host's length % 4 != 0 or length == 0
            else:
                raise RuntimeError("Not enough workers to host an encrypted model!")
        # If model isn't a plan
        else:
            raise RuntimeError("Model need to be a plan to be encrypted!")

    def _serve_non_encrypted_model(self, model, model_id):
        """ This method will choose one of grid nodes registered in the grid network to host a plain text model.
            Args:
                model : Model to be hosted.
                model_id : Model's ID.
        """
        # Perform a request to choose model's host
        response = requests.get(self.gateway_url + "/choose-model-host")
        hosts = json.loads(response.content)

        for host_id, host_address in hosts:
            # Host model
            host_worker = self.__connect_with_node(host_id, host_address)
            host_worker.serve_model(model, model_id=model_id)
            host_worker.disconnect()

    def run_inference(self, model_id, dataset, encrypted=False, copy=True):
        """
            Run data inference with plain text / encrypted data.

            Args:
                model_id: Model's ID.
                dataset: Dataset to be inferred.
                encrypted: Boolean flag to choose encrypted model.
                copy: Boolean flag to perform encrypted inference without lose plan.
            Returns:
                Tensor: Inference's result.
        """
        # Encrypted Models
        if encrypted:
            result = self._run_encrypted_inference(model_id, dataset, copy=copy)
        # Non Encrypted Models
        else:
            result = self._run_non_encrypted_inference(model_id, dataset)
        return result

    def _run_encrypted_inference(self, model_id, dataset, copy=True):
        """ Search for an encrypted model and perform inference.
            
            Args:
                model_id: Model's ID.
                dataset: Dataset to be shared/inferred.
                copy: Boolean flag to perform encrypted inference without lose plan.
            Returns:
                Tensor: Inference's result.
        """
        # Search for an encrypted model
        body = json.dumps({"model_id": model_id})

        response = requests.post(
            self.gateway_url + "/search-encrypted-model", data=body
        )

        match_nodes = json.loads(response.content)
        if len(match_nodes):
            # Host of encrypted plan
            node_id = list(match_nodes.keys())[0]  # Get the first one
            node_address = match_nodes[node_id]["address"]

            # Workers with SMPC parameters tensors
            worker_infos = match_nodes[node_id]["nodes"]["workers"]
            crypto_provider = match_nodes[node_id]["nodes"]["crypto_provider"]

            # Connect with host node
            host_node = self.__connect_with_node(node_id, node_address)

            # Connect with SMPC Workers
            workers = []
            for worker_id, worker_address in worker_infos:
                workers.append(self.__connect_with_node(worker_id, worker_address))

            # Connect with SMPC crypto provider
            crypto_provider_id = crypto_provider[0]
            crypto_provider_url = crypto_provider[1]

            crypto_node = self.__connect_with_node(
                crypto_provider_id, crypto_provider_url
            )

            # Share your dataset to same SMPC Workers
            shared_dataset = dataset.fix_precision().share(
                *workers, crypto_provider=crypto_node
            )

            # Perform Inference
            fetched_plan = sy.hook.local_worker.fetch_plan(
                model_id, host_node, copy=copy
            )
            return fetched_plan(shared_dataset).get().float_prec()
        else:
            raise RuntimeError("Model not found on Grid Network!")

    def _run_non_encrypted_inference(self, model_id, dataset):
        """ This method will search for a specific model registered on grid network, if found,
            It will run inference.
            Args:
                model_id : Model's ID.
                dataset : Data used to run inference.
            Returns:
                Tensor : Inference's result.
        """
        worker = self.query_model(model_id)
        if worker:
            response = worker.run_inference(model_id=model_id, data=dataset)
            worker.disconnect()
            return torch.tensor(response["prediction"])
        else:
            raise RuntimeError("Model not found on Grid Network!")

    def query_model(self, model_id):
        """ This method will search for a specific model registered on grid network, if found,
            It will return all grid nodes that contains the desired model.
            Args:
                model_id : Model's ID.
                data : Data used to run inference.
            Returns:
                workers : List of workers that contains the desired model.
        """
        # Search for a model
        body = json.dumps({"model_id": model_id})

        response = requests.post(self.gateway_url + "/search-model", data=body)

        match_nodes = json.loads(response.content)
        if len(match_nodes):
            node_id, node_url = match_nodes[0]  # Get the first node
            worker = self.__connect_with_node(node_id, node_url)
        else:
            worker = None
        return worker

    def __connect_with_node(self, node_id, node_url):
        if node_id not in sy.hook.local_worker._known_workers:
            worker = WebsocketGridClient(sy.hook, node_url, node_id)
            worker.connect()
        else:
            # There is already a connection to this node
            worker = sy.hook.local_worker._known_workers[node_id]
            worker.connect()
        return worker

    def disconnect_nodes(self):
        for node in sy.hook.local_worker._known_workers:
            if isinstance(
                sy.hook.local_worker._known_workers[node], WebsocketGridClient
            ):
                sy.hook.local_worker._known_workers[node].disconnect()
