import glob
import json
import os
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urljoin

import click
import requests

from .providers import AZURE, GCP, AWS_Serverfull, AWS_Serverless
from .providers.aws import utils as aws_utils
from .providers.azure import utils as azure_utils
from .providers.gcp import utils as gcp_utils

from .utils import COLORS, Config, colored

pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option(
    "--output-file", default=f"config_{time.strftime('%Y-%m-%d_%H%M%S')}.json"
)
@pass_config
def cli(config: SimpleNamespace, output_file: str):
    """OpenMined CLI for Infrastructure Management.

    Example:

    >>> pygrid deploy --provider aws --app domain

    >>> pygrid deploy --provider azure --app network
    """
    click.echo(colored("Welcome to OpenMined PyGrid CLI", color=COLORS.blue))
    ## ROOT Directory
    config.pygrid_root_path = str(Path.home() / ".pygrid/cli/")
    os.makedirs(config.pygrid_root_path, exist_ok=True)
    config.output_file = f"{config.pygrid_root_path}/{output_file}"


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
    default="Domain",
    type=click.Choice(["Domain", "Network"], case_sensitive=False),
    help="The PyGrid App to be deployed",
)
@pass_config
def deploy(config: SimpleNamespace, provider: str, app: str):
    """CLI PyGrid Apps Deployment.

    Example:

    >>> pygrid deploy --provider aws --app domain

    >>> pygrid deploy --provider azure --app network
    """

    config.provider = provider.lower()

    # Store credentials in a separate object, thus not logging it in output
    # when asking the user to confirm the current configuration
    credentials = Config()

    # credentials file
    with open(
        click.prompt(
            f"Please enter path to your  {colored(f'{config.provider} credentials')} json file",
            type=str,
            default=f"{Path.home()}/.{config.provider}/credentials.json",
        ),
        "r",
    ) as f:
        credentials.cloud = json.load(f)

    ## Get app config and arguments
    config.app = Config(name=app.lower())

    ## Deployment type
    config.serverless = False
    if config.app.name == "network":
        config.serverless = click.confirm(f"Do you want to deploy serverless?")

    ## Websockets
    if not config.serverless:
        config.websockets = click.confirm(f"Will you need to support Websockets?")

    if not config.serverless:
        get_app_arguments(config)

    ## Prompting user to provide configuration for the selected cloud
    if config.provider == "aws":
        config.vpc = aws_utils.get_vpc_config()
        if not config.serverless:
            config.vpc.instance_type = aws_utils.get_instance_type(config.vpc.region)
    elif config.provider == "gcp":
        config.gcp = gcp_utils.get_gcp_config()
    elif config.provider == "azure":
        config.azure = azure_utils.get_azure_config()

    ## Database
    credentials.db = aws_utils.get_db_config()

    ## TODO(amr): [clean] For quick dev stuff
    # with open("/Users/amrmkayid/.pygrid/cli/config_azure.json", "rb") as config_json:
    #     config = Config(**json.load(config_json))

    if click.confirm(
        f"""Your current configration are:
        \n\n{colored((json.dumps(vars(config),
                        indent=2, default=lambda o: o.__dict__)))}
        \n\nContinue?"""
    ):

        # config.credentials = credentials
        click.echo(colored("START DEPLOYINGGG... 🔃", color=COLORS.red))

        if config.provider == "aws":
            deployment = (
                AWS_Serverless(config)
                if config.serverless
                else AWS_Serverfull(config=config)
            )
        elif config.provider == "azure":
            deployment = AZURE(config)
        elif config.provider == "gcp":
            deployment = GCP(config)

        if deployment.validate():
            deployed, output = deployment.deploy()
        else:
            deployed, output = (
                False,
                {"failure": f"Your attempt to deploy PyGrid {config.app.name} failed"},
            )
        click.echo(
            f"""\n\n\nYour deployment has {'successed' if deployed else 'failed'}
            \n\n\nPlease check the output below for more details"""
        )
        click.echo(output)


def get_app_arguments(config):
    config.app.count = click.prompt(
        f"How many apps do you want to deploy", type=int, default=1
    )
    apps = []
    for count in range(1, config.app.count + 1):
        if config.app.name == "domain":
            id = click.prompt(
                f"#{count}: PyGrid Domain ID",
                type=str,
                default=os.environ.get("DOMAIN_ID", None),
            )
            port = click.prompt(
                f"#{count}: Port number of the socket.io server",
                type=str,
                default=os.environ.get("GRID_DOMAIN_PORT", 5000),
            )
            host = click.prompt(
                f"#{count}: Grid DOMAIN host",
                type=str,
                default=os.environ.get("GRID_DOMAIN_HOST", "0.0.0.0"),
            )
            app = Config(id=id, port=port, host=host)
        elif config.app.name == "network":
            port = click.prompt(
                f"#{count}: Port number of the socket.io server",
                type=str,
                default=os.environ.get("GRID_NETWORK_PORT", f"{7000 + count}"),
            )
            host = click.prompt(
                f"#{count}: Grid Network host",
                type=str,
                default=os.environ.get("GRID_NETWORK_HOST", "0.0.0.0"),
            )
            app = Config(port=port, host=host)
        else:
            port = click.prompt(
                f"#{count}: Port number of the socket.io server",
                type=str,
                default=os.environ.get("GRID_WORKER_PORT", 5000),
            )
            host = click.prompt(
                f"#{count}: Grid DOMAIN host",
                type=str,
                default=os.environ.get("GRID_WORKER_HOST", "0.0.0.0"),
            )
            app = Config(port=port, host=host)

        apps.append(app)
    config.apps = apps


@cli.resultcallback()
@pass_config
def logging(config, results, **kwargs):
    click.echo(f"Writing configs to {config.output_file}")
    with open(config.output_file, "w", encoding="utf-8") as f:
        json.dump(vars(config), f, indent=2, default=lambda o: o.__dict__)
