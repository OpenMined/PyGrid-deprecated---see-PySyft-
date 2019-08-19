"""
This file exists to provide one common place for all http requests
"""
import binascii
import json

from flask import render_template
from flask import Response
from flask import request
import syft as sy

from . import main
from . import hook

import torch

models = {}


@main.route("/identity/")
def is_this_an_opengrid_node():
    """This exists because in the automation scripts which deploy nodes,
    there's an edge case where the 'node already exists' but sometimes it
    can be an app that does something totally different. So we want to have
    some endpoint which just casually identifies this server as an OpenGrid
    server."""
    return "OpenGrid"


@main.route("/models/<model_name>", methods=["GET"])
def post(model_name):
    if model_name not in models:
        return Response(
            json.dumps({"UnknownModel": "Unknown model {}".format(model_name)}),
            status=404,
            mimetype="application/json",
        )

    model = models[model_name]
    serialized_data = request.form["data"].encode("ISO-8859-1")
    data = sy.serde.deserialize(serialized_data)

    response = model(data).detach().numpy().tolist()
    return Response(
        json.dumps({"prediction": response}), status=200, mimetype="application/json"
    )


@main.route("/serve-model/", methods=["POST"])
def serve_model():
    serialized_model = request.form["model"].encode("ISO-8859-1")
    model_name = request.form["model_name"]

    deserialized_model = sy.serde.deserialize(serialized_model)

    # TODO store this in a local database
    models[model_name] = deserialized_model

    return Response(
        json.dumps({"success": True}), status=200, mimetype="application/json"
    )


@main.route("/", methods=["GET"])
def index():
    """Index page."""
    return render_template("index.html")
