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
    if result["success"]:
        return Response(json.dumps(result), status=200, mimetype="application/json")
    else:
        return Response(json.dumps(result), status=404, mimetype="application/json")


@main.route("/models/", methods=["GET"])
def list_models():
    """Generates a list of models currently saved at the worker"""
    return Response(
        json.dumps(mm.list_models()), status=200, mimetype="application/json"
    )


@main.route("/models/<model_id>", methods=["GET"])
def model_inference(model_id):

    response = mm.get_model_with_id(model_id)
    # check if model exists. Else return a unknown model response.
    if response["success"]:
        # deserialize the model from binary so we may use it.
        model = sy.serde.deserialize(response["model"])
        # serializing the data from GET request
        serialized_data = request.form["data"].encode("ISO-8859-1")
        data = sy.serde.deserialize(serialized_data)

        # If we're using a Plan we need to register the object
        # to the local worker in order to execute it
        sy.hook.local_worker.register_obj(data)

        predictions = model(data).detach().numpy().tolist()

        # We can now remove data from the objects
        del data
        return Response(
            json.dumps({"success": True, "prediction": predictions}),
            status=200,
            mimetype="application/json",
        )
    else:
        return Response(json.dumps(response), status=404, mimetype="application/json")


@main.route("/serve-model/", methods=["POST"])
def serve_model():
    encoding = request.form["encoding"]
    serialized_model = request.form["model"].encode(encoding)
    model_id = request.form["model_id"]

    # save the model for later usage
    response = mm.save_model(serialized_model, model_id)
    if response["success"]:
        return Response(json.dumps(response), status=200, mimetype="application/json")
    else:
        return Response(json.dumps(response), status=500, mimetype="application/json")


@main.route("/", methods=["GET"])
def index():
    """Index page."""
    return render_template("index.html")


@main.route("/dataset-tags", methods=["GET"])
def get_available_tags():
    """ Returns all tags stored in this node. Can be very useful to know what datasets this node contains. """
    available_tags = set()
    objs = hook.local_worker._objects

    for key, obj in objs.items():
        if obj.tags:
            available_tags.update(set(obj.tags))

    return Response(
        json.dumps(list(available_tags)), status=200, mimetype="application/json"
    )


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
