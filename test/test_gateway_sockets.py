import pytest
import json
import websockets
import aiounittest

from test import GATEWAY_PORT

class GatewaySocketsTest(aiounittest.AsyncTestCase):

    async def test_socket_ping(self):
        async with websockets.connect(f"ws://localhost:{GATEWAY_PORT}") as websocket:
            await websocket.send(json.dumps({"type": "socket-ping", "data": {}}))
            message = await websocket.recv()
            self.assertEqual(message, json.dumps({"alive": "True"}))

    def test_webrtc_join_room(self):
        pass

    def test_webrtc_left_room(self):
        pass

    def test_webrtc_internal_message(self):
        pass

