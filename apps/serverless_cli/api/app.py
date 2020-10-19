import json
from flask import Flask, request, Response

app = Flask(__name__)


@app.route("/")
def deploy_node():
    print(type(request.values))
    print(request.values)
    provider = request.values.get("provider", type=str, default=None)
    id = request.values.get("id", type=str, default=None)
    port = request.values.get("port", type=str, default="5000")
    host = request.values.get("host", type=str, default="0.0.0.0")
    network = request.values.get("network", type=str, default=None)
    websockets = request.values.get("websockets", type=bool, default=False)
    serverless = request.values.get("serverless", type=bool, default=False)
    if provider is None:
        return Response(
            json.dumps({"Error": "Please provide a valid cloud provdier"}),
            status=400,  # Bad Request
            mimetype="application/json",
        )

    response = {}
    # respsonse = deploy()

    return Response(json.dumps(response), status=200, mimetype="application/json")


if __name__ == "__main__":
    app.run(debug=True)
