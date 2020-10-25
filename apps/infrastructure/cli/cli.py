import json
import os
from pprint import pformat

import click
import requests
import terrascript
import subprocess

from .provider_utils import aws
from .provider_utils import azure
from .provider_utils import gcp

# from .providers.aws import AWS
# from .providers.azure import AZURE
# from .providers.gcp import GCP
from .utils import COLORS, Config, colored

pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option("--output-file", default="config.json")
@pass_config
def cli(config, output_file):
    """OpenMined CLI for Infrastructure Management.

    Example:

    >>> pygrid deploy --provider aws --app node

    >>> pygrid deploy --provider azure --app network
    """
    click.echo(colored("Welcome to OpenMined PyGrid CLI!"))
    config.output_file = output_file


@cli.command()
@click.option(
    "--provider",
    prompt="Cloud Provider: ",
    default="AWS",
    type=click.Choice(["AWS", "GCP", "AZURE"], case_sensitive=False),
    help="The Cloud Provider for the deployment",
)
@click.option(
    "--app",
    prompt="PyGrid App: ",
    default="Node",
    type=click.Choice(["Node", "Network", "Worker"], case_sensitive=False),
    help="The PyGrid App to be deployed",
)
@pass_config
def deploy(config, provider, app):
    config.provider = provider.lower()

    ## Get app config and arguments
    config.app = Config(name=app.lower())
    get_app_arguments(config)

    ## credentials file
    config.credentials = click.prompt(
        f"Please enter a your cloud deployment {colored('credentials')} file",
        type=str,
        default=f"~/.{config.provider}/credentials.json",
    )

    ## Websockets
    if click.confirm(f"Will you need to support Websockets?"):
        config.websockets = True
    else:
        config.websockets = False

    ## Deployment type
    if click.confirm(f"Do you want to deploy serverless?"):
        config.deployment_type = "serverless"
    else:
        config.deployment_type = "serverfull"

    ## Prompting user to provide configuration for the selected cloud
    if config.provider == "aws":
        # config.vpc = aws.get_vpc_config()
        config.vpc = Config(region="us-east-1", av_zones=["us-east-1a", "us-east-1b"])
        config.db = aws.get_db_config()
    elif config.provider == "gcp":
        pass
    elif config.provider == "azure":
        pass

    if click.confirm(
        f"""Your current configration are: \n\n{colored((json.dumps(vars(config), indent=2, default=lambda o: o.__dict__)))} \n\nContinue?"""
    ):

        data = json.dumps(vars(config), indent=2, default=lambda o: o.__dict__)

        url = "http://localhost:5000/"
        r = requests.post(url, json=data)

        if r.status_code == 200:
            print(f"Your PyGrid {config.app.name} was deployed successfully")
        else:
            print(
                f"There was an issue with deploying your Pygrid {config.app.name}. Please try again."
            )

        ### For dev purpose
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


def get_app_arguments(config):
    if config.app.name == "node":
        config.app.id = click.prompt(
            f"PyGrid Node ID", type=str, default=os.environ.get("NODE_ID", None)
        )
        config.app.port = click.prompt(
            f"Port number of the socket.io server",
            type=str,
            default=os.environ.get("GRID_NODE_PORT", 5000),
        )
        config.app.host = click.prompt(
            f"Grid node host",
            type=str,
            default=os.environ.get("GRID_NODE_HOST", "0.0.0.0"),
        )
        config.app.network = click.prompt(
            f"Grid Network address (e.g. --network=0.0.0.0:7000)",
            type=str,
            default=os.environ.get("NETWORK", None),
        )
        # TODO: Validate if this is related to data-centric or model-centric
        # config.app.num_replicas = click.prompt(
        #     f"Number of replicas to provide fault tolerance to model hosting",
        #     type=int,
        #     default=os.environ.get("NUM_REPLICAS", None),
        # )
    elif config.app.name == "network":
        config.app.port = click.prompt(
            f"Port number of the socket.io server",
            type=str,
            default=os.environ.get("GRID_NETWORK_PORT", "7000"),
        )
        config.app.host = click.prompt(
            f"Grid Network host",
            type=str,
            default=os.environ.get("GRID_NETWORK_HOST", "0.0.0.0"),
        )
    else:
        # TODO: Workers arguments
        pass


@cli.resultcallback()
@pass_config
def logging(config, results, **kwargs):
    click.echo(f"Writing configs to {config.output_file}")
    with open(config.output_file, "w", encoding="utf-8") as f:
        json.dump(vars(config), f, indent=2, default=lambda o: o.__dict__)
