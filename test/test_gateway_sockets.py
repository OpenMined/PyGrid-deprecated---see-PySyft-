import unittest
import pytest
import grid as gr
import json
from socket import socket, AF_INET, SOCK_STREAM
from test import GATEWAY_PORT, GATEWAY_URL


class GatewaySocketsTest(unittest.TestCase):
    def setUp(self):
        self.my_grid = gr.GridNetwork(GATEWAY_URL)
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect(("", int(GATEWAY_PORT)))

    def tearDown(self):
        self.client_socket.close()

    def test_get_protocol(self):
        pass

    def test_webrtc_join_room(self):
        pass

    def test_webrtc_left_room(self):
        pass

    def test_webrtc_internal_message(self):
        pass
