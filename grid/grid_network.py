import requests
import json
import syft as sy
from grid.websocket_client import WebsocketGridClient

class GridNetwork(object):
    '''  The purpose of the Grid Network class is to control the entire communication flow by abstracting operational steps.
    
        Attributes:
            - gateway_url : network address to which you want to connect
            - connected_grid_nodes : Grid nodes that are connected to the application.
    '''
    def __init__(self, gateway_url):
        self.gateway_url = gateway_url
        self.connected_grid_nodes = {}

    def search(self,*query):
        ''' Search a set of tags across the grid network 
            
            Parameters:
                query : A set of dataset tags
            Return:
                tensor_set : matrix of tensor pointers
        '''
        body = json.dumps({ "query": list(query) })
        
        # Asks to grid gateway about dataset-tags
        response = requests.post(self.gateway_url + "/search", data=body )
        
        # List of nodes that contains the desired dataset
        match_nodes = json.loads(response.content)
        
        # Connect with grid nodes that contains the dataset and get their pointers
        tensor_set = []
        for node in match_nodes:
            worker = WebsocketGridClient(sy.hook, node[1], node[0])
            
            # Connection already exists
            if(node[0] not in self.connected_grid_nodes):
                self.connected_grid_nodes[node[0]] = worker
                worker.connect()
            else:
                # There is already a connection to this node
                worker = self.connected_grid_nodes[node[0]]
            tensor_set.append(worker.search(*query))
        return tensor_set

    def disconnect_nodes(self):
        for node in self.connected_grid_nodes:
            self.connected_grid_nodes[node].disconnect()
