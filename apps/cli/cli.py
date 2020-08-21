import json

import click

from .utils import COLORS, Config

pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option("--output-file", default="config.json")
@pass_config
def cli(config, output_file):
    """
    OpenMined CLI for Infrastructure Management

    Example:

    >>> pygrid deploy node --provider aws

    >>> pygrid deploy network --provider azure
    """
    click.echo(
        click.style(f"Welcome to OpenMined PyGrid CLI!", fg=COLORS.green, bold=True)
    )
    config.output_file = output_file


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


@cli.resultcallback()
@pass_config
def logging(config, results, **kwargs):
    click.echo(f"Writing resutls to {config.output_file}")
    with open(config.output_file, "w", encoding="utf-8") as f:
        json.dump(vars(config), f)
