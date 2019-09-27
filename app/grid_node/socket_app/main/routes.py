from . import html


@html.route("/")
def hello():
    return "Hello World!"
