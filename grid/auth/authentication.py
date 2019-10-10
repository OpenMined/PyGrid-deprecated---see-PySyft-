from abc import ABC


class BaseAuthentication(ABC):
    def __init__(self, filename):
        self.FILENAME = filename

    def parse(self):
        raise NotImplementedError("Parse not specified!")

    def json(self):
        raise NotImplementedError("JSON not specified!")
