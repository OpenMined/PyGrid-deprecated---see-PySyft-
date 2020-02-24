"""
    All Gateway routes (REST API).
"""

from flask import render_template, Response, request, current_app
from . import main
import json
import random
import os
import requests

from .persistence.manager import register_new_node, connected_nodes, delete_node
from .processes import processes
from .events import handler
from .auth import workers

# All grid nodes registered at grid network will be stored here
grid_nodes = {}

SMPC_HOST_CHUNK = 4  # Minimum nodes required to host an encrypted model
INVALID_JSON_FORMAT_MESSAGE = (
    "Invalid JSON format."  # Default message used to report Invalid JSON format.
)
INVALID_REQUEST_KEY_MESSAGE = (
    "Invalid request key."  # Default message for invalid request key.
)
INVALID_PROTOCOL_MESSAGE = "Protocol is None or the id does not exist."


@main.route("/", methods=["GET"])
def index():
    """ Main Page. """
    return render_template("index.html")


@main.route("/join", methods=["POST"])
def join_grid_node():
    """ Register a new grid node at grid network.
        TODO: Add Authentication process.
    """

    response_body = {"message": None}
    status_code = None

    try:
        data = json.loads(request.data)
        # Register new node
        if register_new_node(data["node-id"], data["node-address"]):
            response_body["message"] = "Successfully Connected!"
            status_code = 200
        else:  # Grid ID already registered
            response_body["message"] = "This ID has already been registered"
            status_code = 409

    # JSON format not valid.
    except ValueError or KeyError as e:
        response_body["message"] = INVALID_JSON_FORMAT_MESSAGE
        status_code = 400

    return Response(
        json.dumps(response_body), status=status_code, mimetype="application/json"
    )


@main.route("/connected-nodes", methods=["GET"])
def get_connected_nodes():
    print("yolo2")
    """ Get a list of connected nodes. """
    grid_nodes = connected_nodes()
    return Response(
        json.dumps({"grid-nodes": list(grid_nodes.keys())}),
        status=200,
        mimetype="application/json",
    )


@main.route("/delete-node", methods=["DELETE"])
def delete_grid_note():
    """ Delete a grid node at grid network"""

    response_body = {"message": None}
    status_code = None

    try:
        data = json.loads(request.data)

        # Register new node
        if delete_node(data["node-id"], data["node-address"]):
            response_body["message"] = "Successfully Deleted!"
            status_code = 200
        else:  # Grid ID was not found
            response_body["message"] = "This ID was not found in connected nodes"
            status_code = 409

    # JSON format not valid.
    except ValueError or KeyError as e:
        response_body["message"] = INVALID_JSON_FORMAT_MESSAGE
        status_code = 400

    return Response(
        json.dumps(response_body), status=status_code, mimetype="application/json"
    )


@main.route("/choose-encrypted-model-host", methods=["GET"])
def choose_encrypted_model_host():
    """ Used to choose grid nodes to host an encrypted model
        PS: currently we perform this randomly
    """
    grid_nodes = connected_nodes()
    n_replica = current_app.config["N_REPLICA"]

    if not n_replica:
        n_replica = 1
    try:
        hosts = random.sample(list(grid_nodes.keys()), n_replica * SMPC_HOST_CHUNK)
        hosts_info = [(host, grid_nodes[host]) for host in hosts]
    # If grid network doesn't have enough grid nodes
    except ValueError:
        hosts_info = []

    return Response(json.dumps(hosts_info), status=200, mimetype="application/json")


@main.route("/choose-model-host", methods=["GET"])
def choose_model_host():
    """ Used to choose some grid node to host a model.
        PS: Currently we perform this randomly.
    """
    grid_nodes = connected_nodes()
    n_replica = current_app.config["N_REPLICA"]
    if not n_replica:
        n_replica = 1

    model_id = request.args.get("model_id")
    hosts_info = None

    # lookup the nodes already hosting this model to prevent hosting different model versions
    if model_id:
        hosts_info = _get_model_hosting_nodes(model_id)

    # no model id given or no hosting nodes found: randomly choose node
    if not hosts_info:
        hosts = random.sample(list(grid_nodes.keys()), n_replica)
        hosts_info = [(host, grid_nodes[host]) for host in hosts]

    return Response(json.dumps(hosts_info), status=200, mimetype="application/json")


@main.route("/search-encrypted-model", methods=["POST"])
def search_encrypted_model():
    """ Search for an encrypted plan model on the grid network, if found,
        returns host id, host address and SMPC workers infos.
    """

    response_body = {"message": None}
    status_code = None

    try:
        body = json.loads(request.data)

        grid_nodes = connected_nodes()
        match_nodes = {}
        for node in grid_nodes:
            try:
                response = requests.post(
                    os.path.join(grid_nodes[node], "search-encrypted-models"),
                    data=request.data,
                )
            except requests.exceptions.ConnectionError:
                continue

            response = json.loads(response.content)

            # If workers / crypto_provider fields in response dict
            if not len({"workers", "crypto_provider"} - set(response.keys())):
                match_nodes[node] = {"address": grid_nodes[node], "nodes": response}

            response_body = match_nodes
            status_code = 200

    # JSON format not valid.
    except ValueError or KeyError as e:
        response_body["message"] = INVALID_JSON_FORMAT_MESSAGE
        status_code = 400

    return Response(
        json.dumps(response_body), status=status_code, mimetype="application/json"
    )


@main.route("/search-model", methods=["POST"])
def search_model():
    """ Search for a plain text model on the grid network. """

    response_body = {"message": None}
    status_code = None

    try:
        body = json.loads(request.data)

        model_id = body["model_id"]
        match_nodes = _get_model_hosting_nodes(model_id)

        # It returns a list[ (id, address) ]  with all grid nodes that have the desired model
        response_body = match_nodes
        status_code = 200

    except ValueError or KeyError:
        response_body["message"] = INVALID_JSON_FORMAT_MESSAGE
        status_code = 400

    return Response(
        json.dumps(response_body), status=status_code, mimetype="application/json"
    )


@main.route("/search-available-models", methods=["GET"])
def available_models():
    """ Get all available models on the grid network. Can be useful to know what models our grid network have. """
    grid_nodes = connected_nodes()
    models = set()
    for node in grid_nodes:
        try:
            response = requests.get(grid_nodes[node] + "/models/").content
        except requests.exceptions.ConnectionError:
            continue
        response = json.loads(response)
        models.update(set(response.get("models", [])))

    # Return a list[ "model_id" ]  with all grid nodes
    return Response(json.dumps(list(models)), status=200, mimetype="application/json")


@main.route("/search-available-tags", methods=["GET"])
def available_tags():
    """ Returns all available tags stored on grid nodes. Can be useful to know what dataset our grid network have. """
    grid_nodes = connected_nodes()
    tags = set()
    for node in grid_nodes:
        try:
            response = requests.get(grid_nodes[node] + "/dataset-tags").content
        except requests.exceptions.ConnectionError:
            continue
        response = json.loads(response)
        tags.update(set(response))

    # Return a list[ "#tags" ]  with all grid nodes
    return Response(json.dumps(list(tags)), status=200, mimetype="application/json")


@main.route("/search", methods=["POST"])
def search_dataset_tags():
    """ Search for information on all known nodes and return a list of the nodes that own it. """

    response_body = {"message": None}
    status_code = None

    try:
        body = json.loads(request.data)
        grid_nodes = connected_nodes()

        # Perform requests (HTTP) to all known nodes looking for the desired data tag
        match_grid_nodes = []
        for node in grid_nodes:
            try:
                response = requests.post(
                    grid_nodes[node] + "/search",
                    data=json.dumps({"query": body["query"]}),
                ).content
            except requests.exceptions.ConnectionError:
                continue
            response = json.loads(response)
            # If contains
            if response["content"]:
                match_grid_nodes.append((node, grid_nodes[node]))

        # It returns a list[ (id, address) ]  with all grid nodes that have the desired data
        response_body = match_grid_nodes
        status_code = 200

    except ValueError or KeyError as e:
        response_body["message"] = INVALID_JSON_FORMAT_MESSAGE
        status_code = 400

    return Response(json.dumps(response_body), status=200, mimetype="application/json")


@main.route("/federated/get-protocol", methods=["GET"])
def download_protocol():
    """Request a download of a protocol"""

    response_body = {"message": None}
    status_code = None

    worker_id = request.args.get("worker_id")
    request_key = request.args.get("request_key")
    protocol_id = request.args.get("protocol_id")

    _worker = workers.get_worker(worker_id)

    _cycle = None
    if _worker:
        _cycle = _worker.get_cycle(request_key)

    if _cycle:
        protocol_res = _cycle.fl_process.json()["client_protocols"]
        if protocol_res != None and protocol_id in protocol_res.keys():
            return Response(
                json.dumps(protocol_res[protocol_id]),
                status=200,
                mimetype="application/json",
            )
        else:
            response_body["message"] = INVALID_PROTOCOL_MESSAGE
            status_code = 400

            return Response(
                json.dumps(response_body),
                status=status_code,
                mimetype="application/json",
            )
    else:
        response_body["message"] = INVALID_REQUEST_KEY_MESSAGE
        status_code = 400

        return Response(
            json.dumps(response_body), status=status_code, mimetype="application/json"
        )


def _get_model_hosting_nodes(model_id):
    """ Search all nodes if they are currently hosting the model.

    :param model_id: The model to search for
    :return: An array of the nodes currently hosting the model
    """
    grid_nodes = connected_nodes()
    match_nodes = []
    for node in grid_nodes:
        try:
            response = requests.get(grid_nodes[node] + "/models/").content
        except requests.exceptions.ConnectionError:
            continue
        response = json.loads(response)
        if model_id in response.get("models", []):
            match_nodes.append((node, grid_nodes[node]))

    return match_nodes


@main.route("/federated/get-model", methods=["GET"])
def download_model():
    """ validate request key and download model
    """

    model_id = request.args.get("model_id")
    worker_id = request.args.get("worker_id")
    request_key = request.args.get("request_key")

    _worker = workers.get_worker(worker_id)

    _cycle = None
    if _worker:
        _cycle = _worker.get_cycle(request_key)

    # If the worker own a cycle matching with the request_key
    if _cycle:
        return Response(
            json.dumps(_cycle.fl_process.json()["model"]),
            status=200,
            mimetype="application/json",
        )
    else:
        response_body = {"message": None}
        response_body["message"] = INVALID_REQUEST_KEY_MESSAGE
        status_code = 400

        return Response(
            json.dumps(response_body), status=status_code, mimetype="application/json"
        )


@main.route("/req_join", methods=["GET"])
def fl_cycle_application_decision():
    """
        use the temporary req_join endpoint to mockup:
        - reject if worker does not satisfy 'minimum_upload_speed' and/or 'minimum_download_speed'
        - is a part of current or recent cycle according to 'do_not_reuse_workers_until_cycle'
        - selects according to pool_selection
        - is under max worker (with some padding to account for expected percent of workers so do not report successfully)
    """

    # parse query strings (for now), evetually this will be parsed from the request body
    model_id = request.args.get("model_id")
    up_speed = request.args.get("up_speed")
    down_speed = request.args.get("down_speed")
    worker_id = request.args.get("worker_id")
    _cycle = processes.get_cycle(model_id)
    _accept = False
    """
    MVP variable stubs:
        we will stub these with hard coded numbers first, then make functions to dynaically query/update in subsquent PRs
    """
    # this will be replaced with a function that check for the same (model_id, version_#) tuple when the worker last participated
    last_participation = 1
    # how late is too late into the cycle time to give a worker "new work", if only 5 seconds left probably don't bother, set this intelligently later
    MINIMUM_CYCLE_TIME_LEFT = 500
    # the historical amount of workers that fail to report (out of time, offline, too slow etc...),
    # could be modified to be worker/model specific later, track across overall pygrid instance for now
    EXPECTED_FAILURE_RATE = 0.2

    # dummy function to ping worker, to be replaced with a function that actually pings the worker and verifies connection
    async def ping_worker(worker_id):
        return await handler.connections[
            worker_id
        ].ping()  # TODO@Maddie: ask Patrick about success / failure of ping, just return is good or?

    dummy_server_config = {
        "max_workers": 100,
        "pool_selection": "random",  # or "iterate"
        "num_cycles": 5,
        "do_not_reuse_workers_until_cycle": 4,
        "cycle_length": 8 * 60 * 60,  # 8 hours
        "minimum_upload_speed": 2000,  # 2 mbps
        "minimum_download_speed": 4000,  # 4 mbps
    }

    """  end of variable stubs """

    _server_config = dummy_server_config

    up_speed_check = up_speed > _server_config["minimum_upload_speed"]
    down_speed_check = down_speed > _server_config["minimum_download_speed"]
    ping_check = ping_worker(worker_id)
    cycle_valid_check = (
        (
            last_participation + _server_config["do_not_reuse_workers_until_cycle"]
            >= _cycle.get(
                "cycle_sequence", 99999
            )  # this should reuturn current cycle sequence number
        )
        * (_cycle.get("cycle_sequence", 99999) <= _server_config["num_cycles"])
        * (_cycle.cycle_time > MINIMUM_CYCLE_TIME_LEFT)
        * (worker_id not in _cycle._workers)
    )

    if up_speed_check * down_speed_check * cycle_valid_check * ping_check:
        if _server_config["pool_selection"] == "iterate" and len(
            _cycle._workers
        ) < _server_config["max_workers"] * (1 + EXPECTED_FAILURE_RATE):
            """ first come first serve selection mode """
            _accept = True
        elif (
            _server_config["pool_selection"] == "random"
            and random.random_sample() < 0.8
        ):  # TODO@Maddie: remove magic number, hardcoded for naive probability of accept
            _accept = True
            """
                TODO@Maddie: stub model
                    - model the rate of worker's request to join as lambda in a poisson process
                    - set probabilistic reject rate such that we can expect enough workers will request to join and be accepted
                        - between now and ETA till end of _server_config['cycle_length']
                        - such that we can expect (,say with 95% confidence) successful completion of the cycle
                        - while accounting for EXPECTED_FAILURE_RATE

                        EXPECTED_FAILURE_RATE = moving average with exponential decay (with noised up weights for security)
                        k' = max_workers * (1+EXPECTED_FAILURE_RATE) # expected failure adjusted max_workers
                        T_left = T_end - T_now # how much time is left (in the same unit as below)
                        lambda_actual = (recent) historical rate of request / unit time
                        lambda' = number of requests / unit of time that would satisfy the below equation

                        probability of receiving at least k* requests per unit time:
                            P(K>=k') = 0.95 = e ^ ( - lambda' * T_left) * ( lambda' * T_left) ^ k' / k'! = 1 - P(K<k')

                        solve for lambda':
                            use numerical approximation (newton's method) or just repeatedly call prob = poisson.cdf(x, lambda') via scipy

                        reject_probability = 1 - lambda' / lamba_actual
            """

    if _accept:
        return Response(
            json.dumps(
                {"status": "accepted"}
            ),  # leave out other accpet keys/values for now
            status=200,
            mimetype="application/json",
        )

    # reject by default
    return Response(
        json.dumps(
            {"status": "rejected"}
        ),  # leave out other accpet keys/values for now
        status=400,
        mimetype="application/json",
    )
