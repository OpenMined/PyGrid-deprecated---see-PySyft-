from types import SimpleNamespace


class Config(SimpleNamespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
