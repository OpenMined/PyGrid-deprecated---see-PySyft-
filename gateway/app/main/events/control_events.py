import json


def socket_ping(message: dict) -> str:
    """ Ping request to check node's health state. """
    return json.dumps({"alive": "True"})
