"""All Gateway routes (REST API)."""
from .. import http
from flask import render_template


@http.route("/", methods=["GET"])
def index():
    """Main Page."""
    return "Open Grid Network"
