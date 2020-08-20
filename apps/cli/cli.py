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
