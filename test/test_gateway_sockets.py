import unittest
import pytest
import grid as gr
import json
from test import PORTS, GATEWAY_URL


class GatewaySocketsTest(unittest.TestCase):
    def setUp(self):
        self.my_grid = gr.GridNetwork(GATEWAY_URL)
    
    def tearDown(self):
        self.my_grid.disconnect_nodes()

    def test_get_protocol(self):
        pass

    def test_webrtc_join_room(self):
        pass

    def test_webrtc_left_room(self):
        pass

    def test_webrtc_internal_message(self):
        pass

    
