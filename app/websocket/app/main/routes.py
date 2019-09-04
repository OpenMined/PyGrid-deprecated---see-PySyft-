"""
This file exists to provide one common place for all grid node http requests.
"""
import binascii
import json

from flask import render_template
from flask import Response
from flask import request
import syft as sy

from . import main
from . import hook
from . import model_manager as mm


# TODO(@quisher): Need to document the API using swagger for python "flasgger"


@main.route("/identity/")
def is_this_an_opengrid_node():
    """This exists because in the automation scripts which deploy nodes,
    there's an edge case where the 'node already exists' but sometimes it
    can be an app that does something totally different. So we want to have
    some endpoint which just casually identifies this server as an OpenGrid
    server."""
    return "OpenGrid"


@main.route("/delete_model/", methods=["POST"])
def delete_model():
    model_id = request.form["model_id"]
    result = mm.delete_model(model_id)
    if result is True:
        return Response(
            json.dumps({"status": "success"}), status=200, mimetype="application/json"
        )
    else:
        return Response(
            json.dumps({"status": "failure, file not found"}),
            status=404,
            mimetype="application/json",
        )


@main.route("/models/", methods=["GET"])
def models_list():
    """Generates a list of models currently saved at the worker"""
    return Response(
        json.dumps({"models": mm.models_list()}),
        status=202,
        mimetype="application/json",
    )


@main.route("/models/<model_id>", methods=["GET"])
def model_inference(model_id):

    model = mm.get_model_with_id(model_id)
    # check if model exists. Else return a unknown model response.
    if model is None:
        return Response(
            json.dumps({"UnknownModel": "No model found with id: {}".format(model_id)}),
            status=404,
            mimetype="application/json",
        )
    else:
        # deserialize the model from binary so we may use it.
        model = sy.serde.deserialize(model)
        # serializing the data from GET request
        serialized_data = request.form["data"].encode("ISO-8859-1")
        data = sy.serde.deserialize(serialized_data)

        # If we're using a Plan we need to register the object
        # to the local worker in order to execute it
        sy.hook.local_worker.register_obj(data)

        response = model(data).detach().numpy().tolist()

        # We can now remove data from the objects
        del data
        return Response(
            json.dumps({"prediction": response}),
            status=200,
            mimetype="application/json",
        )


@main.route("/serve-model/", methods=["POST"])
def serve_model():
    encoding = request.form["encoding"]
    serialized_model = request.form["model"].encode(encoding)
    model_id = request.form["model_id"]

    # save the model for later usage
    saving = mm.save_model_for_serving(serialized_model, model_id)
    if saving:
        return Response(
            json.dumps({"success": "Model deployed with id: {}".format(model_id)}),
            status=200,
            mimetype="application/json",
        )
    else:
        return Response(
            json.dumps(
                {
                    "error": "Model ID should be unique. There is already a model being hosted with this id."
                }
            ),
            status=500,
            mimetype="application/json",
        )
    return


@main.route("/", methods=["GET"])
def index():
    """Index page."""
    return render_template("index.html")


@main.route("/search", methods=["POST"])
def search_dataset_tags():
    body = json.loads(request.data)

    # Invalid body
    if "query" not in body:
        return Response("", status=400, mimetype="application/json")

    # Search for desired datasets that belong to this node
    results = hook.local_worker.search(*body["query"])

    body_response = {"content": False}
    if len(results):
        body_response["content"] = True

    return Response(json.dumps(body_response), status=200, mimetype="application/json")
