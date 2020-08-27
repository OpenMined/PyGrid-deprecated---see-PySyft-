from types import SimpleNamespace

import click


class Config(SimpleNamespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


COLORS = SimpleNamespace(
    **{
        "black": "black",
        "red": "red",
        "green": "green",
        "yellow": "yellow",
        "blue": "blue",
        "magenta": "magenta",
        "cyan": "cyan",
        "white": "white",
        "bright_black": "bright_black",
        "bright_red": "bright_red",
        "bright_green": "bright_green",
        "bright_yellow": "bright_yellow",
        "bright_blue": "bright_blue",
        "bright_magenta": "bright_magenta",
        "bright_cyan": "bright_cyan",
        "bright_white": "bright_white",
    }
)


def colored(text, color=COLORS.green, bold=True):
    return click.style(text, fg=color, bold=bold)
