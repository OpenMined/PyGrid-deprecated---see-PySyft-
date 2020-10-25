import json
from flask import Flask, request, Response, jsonify
import terrascript

from .providers import aws

# from .providers import gcp
# from .providers import azure

app = Flask(__name__)


@app.route("/", methods=["POST"])
def index():
    """
    Possible requests:
    Serverfull:
    Node:
    Network:
    Worker:

    Serverless:
    Node:
    {
      "output_file": "config.json",
      "provider": "aws",
      "app": {
        "name": "node",
        "id": "bob",
        "port": 5000,
        "host": "0.0.0.0",
        "network": "0.0.0.0:7000"
      },
      "credentials": "~/.aws/credentials.json",
      "websockets": false,
      "deployment_type": "serverless",
      "aws": {
        "region": "us-east-1",
        "av_zones": [
          "us-east-1a",
          "us-east-1b",
          "us-east-1c"
        ]
      },
      "db": {
        "username": "sachin",
        "password": "lollollol"
      }
    }


    Network:

    {
      "output_file": "config.json",
      "provider": "aws",
      "app": {
        "name": "network",
        "port": "7000",
        "host": "0.0.0.0"
      },
      "credentials": "~/.aws/credentials.json",
      "websockets": false,
      "deployment_type": "serverless",
      "aws": {
        "region": "us-east-1",
        "av_zones": [
          "us-east-1a",
          "us-east-1b",
          "us-east-1c"
        ]
      },
      "db": {
        "username": "sachin",
        "password": "lollollol"
      }
    }
    """

    data = json.loads(request.json)

    provider = data.get("provider").lower()
    app = data.get("app").lower()
    websockets = bool(data.get("websockets"))
    deployment_type = data.get("deployment_type")

    tfscript = terrascript.Terrascript()

    if deployment_type == "serverless":
        if provider == "aws":
            aws.serverless_deployment(tfscript=tfscript)
        else:
            return None

    elif deployment_type == "serverless":
        pass
    # port = data.get("port", type=str, default="5000")
    # host = data.get("host", type=str, default="0.0.0.0")
    # network = data.get("network", type=str, default=None)
    # websockets = data.get("websockets", type=bool, default=False)
    # serverless = data.get("serverless", type=bool, default=False)
    #
    #
    # if provider is None:
    #     return Response(
    #         json.dumps({"Error": "Please provide a valid cloud provdier"}),
    #         status=400,  # Bad Request
    #         mimetype="application/json",
    #     )
    #
    # ## For dev purpose
    # tfscript = terrascript.Terrascript()
    #
    # tfscript += terrascript.provider.aws(
    #     region=config.aws.region, shared_credentials_file=config.credentials
    # )
    # tfscript, vpc, subnets = deploy_vpc(
    #     tfscript, app=config.app.name, av_zones=config.aws.av_zones
    # )
    #
    # if config.deployment_type == "serverless":
    #     tfscript = serverless_deployment(
    #         tfscript,
    #         app=config.app.name,
    #         vpc=vpc,
    #         subnets=subnets,
    #         db_username=config.db.username,
    #         db_password=config.db.password,
    #     )
    # elif config.deployment_type == "serverfull":
    #     pass
    #
    # # write config to file
    # with open("main.tf.json", "w") as tfjson:
    #     json.dump(tfscript, tfjson, indent=2, sort_keys=False)
    #
    # # subprocess.call("terraform init", shell=True)
    # subprocess.call("terraform validate", shell=True)
    # subprocess.call("terraform apply", shell=True)
    response = {"message": "Deployment successful"}
    return Response(json.dumps(response), status=200, mimetype="application/json")


if __name__ == "__main__":
    app.run(debug=True)
