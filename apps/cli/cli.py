import json

import click

from .utils import COLORS, Config, colored

pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option("--output-file", default="config.json")
@pass_config
def cli(config, output_file):
    """OpenMined CLI for Infrastructure Management.

    Example:

    >>> pygrid deploy node --provider aws

    >>> pygrid deploy network --provider azure
    """
    click.echo(colored("Welcome to OpenMined PyGrid CLI!"))
    config.output_file = output_file


@cli.group()
@click.option(
    "--provider",
    prompt="Cloud Provider: ",
    default="AWS",
    type=click.Choice(["AWS", "GCP", "AZURE"], case_sensitive=False),
    help="The Cloud Provider for the deployment",
)
@pass_config
def deploy(config, provider):
    click.echo(f"Starting the deployment on {colored(provider)}...")
    config.provider = provider

    # Deployment Keys
    config.id_key = click.prompt(
        f"Please enter a your cloud deployment {colored('id')} key",
        type=str,
        hide_input=True,
    )
    config.secret_key = click.prompt(
        f"Please enter a your cloud deployment {colored('secret')} key",
        type=str,
        hide_input=True,
    )

    ## Websockets
    if click.confirm(f"Will you need to support Websockets?"):
        if config.provider.lower() != "aws":
            config.deployment_type = "serverfull"
        elif click.confirm(f"Do you want to deploy serverless?"):
            config.deployment_type = "serverless"

    elif click.confirm(f"Do you want to deploy serverless?"):
        click.echo("we are going to serverless deployment!")
        config.deployment_type = "serverless"


@deploy.command()
@pass_config
def node(config):
    click.echo(f"Node Deployment")
    config.app = "Node"


@deploy.command()
@pass_config
def network(config):
    click.echo(f"Network Deployment")
    config.app = "Network"


@cli.resultcallback()
@pass_config
def logging(config, results, **kwargs):
    click.echo(f"Writing configs to {config.output_file}")
    config.id_key = "X" * len(config.id_key)
    config.secret_key = "X" * len(config.secret_key)
    with open(config.output_file, "w", encoding="utf-8") as f:
        json.dump(vars(config), f)
