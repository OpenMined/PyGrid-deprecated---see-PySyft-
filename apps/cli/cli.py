import json

import click

from .utils import COLORS, Config

pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option("--out", default="config.json", type=click.File("w"))
@pass_config
def cli(config, out):
    """
    OpenMined CLI for Infrastructure Management

    Example:

    >>> pygrid deploy node --provider aws

    >>> pygrid deploy network --provider azure
    """
    click.echo(click.style(f"Welcome to OpenMined CLI!", fg=COLORS.green, bold=True))
    json.dump(vars(config), out)


@cli.command()
@click.option("--name", prompt="Your name", help="The person to greet.")
@pass_config
def hello(config, name):
    click.echo(f"Hello {click.style(name, fg=COLORS.red)}!")
    config.name = name


@cli.command()
@click.option(
    "--provider",
    prompt="Cloud Provider: ",
    default="AWS",
    type=click.Choice(["AWS", "GCP", "AZURE"], case_sensitive=False),
    help="The Cloud Provider for the deployment",
)
@pass_config
def deploy(config, provider):
    click.echo(f"Deployment...")
    config.provider = provider
    click.echo(config)
