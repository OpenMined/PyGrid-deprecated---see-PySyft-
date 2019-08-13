from app.websocket.app import create_app
from flask import Flask, session, request, json as flask_json
from flask_socketio import (
    SocketIO,
    send,
    emit,
    join_room,
    leave_room,
    Namespace,
    disconnect,
)

import unittest
import threading
import multiprocessing
import grid as gr
import syft as sy
import torch as th
import time
import requests
import json

hook = sy.TorchHook(th)


gateway_url = "http://localhost:8080"

ports = ["3000", "3001", "3002"]
ids = ["Bob", "Alice", "James"]


def setUpGateway(port):
    import os

    os.environ["SECRET_KEY"] = "Secretkeyhere"
    from gateway.app import create_app

    app = create_app(debug=False)
    app.run(host="0.0.0.0", port="8080")


def setUpNodes(config):
    from app.websocket.app import create_app, socketio

    requests.post(
        gateway_url + "/join",
        data=json.dumps(
            {
                "node-id": config[0],
                "node-address": "http://localhost:" + config[1] + "/",
            }
        ),
    )
    app = create_app(debug=False)
    socketio.run(app, host="0.0.0.0", port=port)


# Init Grid Gateway
p = multiprocessing.Process(target=setUpGateway, args=("8080",))
p.daemon = True
p.start()
time.sleep(5)

# Init Grid Nodes
for (node_id, port) in zip(ids, ports):
    config = (node_id, port)
    p = multiprocessing.Process(target=setUpNodes, args=(config,))
    p.daemon = True
    p.start()

time.sleep(10)


class SocketIOAPITest(unittest.TestCase):
    def setUp(self):
        self.nodes = []
        for (node_id, port) in zip(ids, ports):
            node = gr.WebsocketGridClient(
                hook, "http://localhost:" + port + "/", id=node_id
            )
            node.connect()
            self.nodes.append(node)

    def tearDown(self):
        for node in self.nodes:
            node.disconnect()

    def test_connect_nodes(self):
        try:
            for node in self.nodes:
                for n in self.nodes:
                    if n == node:
                        continue
                    else:
                        node.connect_grid_node(n.uri, n.id)
                        time.sleep(0.2)
        except:
            self.fail("test_connect_nodes : Exception raised!")

    def test_multiple_connections_to_same_node(self):
        try:
            for i in range(10):
                for node in self.nodes:
                    for n in self.nodes:
                        if n == node:
                            continue
                        else:
                            node.connect_grid_node(n.uri, n.id)
                            time.sleep(0.2)
        except:
            self.fail("test_multiple_connections_to_same_node: Exception raised!")

    def test_send_tensor(self):
        x = th.tensor([1, 2, 3, 4])
        x_s = x.send(self.nodes[0])
        self.assertEqual(x_s.location.id, self.nodes[0].id)
        self.assertEqual(x_s.get().tolist(), x.tolist())

    def test_send_tag_tensor(self):
        x = th.tensor([1, 2, 3, 4, 5]).tag("#simple-tensor").describe("Simple tensor")
        y = (
            th.tensor([[4], [5], [7], [8]])
            .tag("#2d-tensor")
            .describe("2d tensor example")
        )
        z = (
            th.tensor([[0, 0, 0, 0, 0]])
            .tag("#zeros-tensor")
            .describe("tensor with zeros")
        )
        w = (
            th.tensor([[0, 0, 0, 0, 0]])
            .tag("#zeros-tensor")
            .describe("tensor with zeros")
        )

        x_s = x.send(self.nodes[0])
        y_s = y.send(self.nodes[1])
        z_s = z.send(self.nodes[2])
        w_s = w.send(self.nodes[0])

        x_s.child.garbage_collect_data = False
        y_s.child.garbage_collect_data = False
        z_s.child.garbage_collect_data = False
        w_s.child.garbage_collect_data = False

        self.assertEqual(x_s.description, "Simple tensor")
        self.assertEqual(y_s.description, "2d tensor example")
        self.assertEqual(z_s.description, "tensor with zeros")
        self.assertEqual(w_s.description, "tensor with zeros")

    def test_move_tensor(self):
        x = th.tensor([1, 2, 3, 4])
        x_s = x.send(self.nodes[0])
        self.assertEqual(x_s.location.id, self.nodes[0].id)
        x1_s = x_s.move(self.nodes[1])
        self.assertEqual(x1_s.location.id, self.nodes[1].id)

    def test_add_remote_tensors(self):
        x = th.tensor([1, 2, 3, 4])
        y = th.tensor([4, 5, 6, 7])
        result = x + y

        x_s = x.send(self.nodes[0])
        y_s = y.send(self.nodes[0])

        result_s = x_s + y_s
        self.assertEqual(result_s.get().tolist(), result.tolist())

    def test_sub_remote_tensors(self):
        x = th.tensor([1, 2, 3, 4, 5])
        y = th.tensor([4, 5, 6, 7, 8])

        result = x - y

        x_s = x.send(self.nodes[0])
        y_s = y.send(self.nodes[0])

        result_s = x_s - y_s
        self.assertEqual(result_s.get().tolist(), result.tolist())

    def test_mul_remote_tensors(self):
        x = th.tensor([1, 2, 3, 4, 5])
        y = th.tensor([4, 5, 6, 7, 8])

        result = x * y

        x_s = x.send(self.nodes[0])
        y_s = y.send(self.nodes[0])

        result_s = x_s * y_s
        self.assertEqual(result_s.get().tolist(), result.tolist())

    def test_exp_remote_tensor(self):
        x = th.tensor([1, 2, 3, 4, 5])
        result = x ** 2

        x_s = x.send(self.nodes[0])
        result_s = x_s ** 2
        self.assertEqual(result_s.get().tolist(), result.tolist())

    def test_div_remote_tensor(self):
        x = th.tensor([1, 2, 3, 4, 5, 6])
        y = th.tensor([2, 4, 6, 8, 10, 12])

        result = x / y

        x_s = x.send(self.nodes[0])
        y_s = y.send(self.nodes[0])

        result_s = x_s / y_s
        self.assertEqual(result_s.get().tolist(), result.tolist())

    def test_share_tensors(self):
        x = th.tensor([1, 2, 3, 4, 5, 6])
        x_s = x.share(self.nodes[0], self.nodes[1], self.nodes[2])
        self.assertTrue(
            [node_id in x_s.child.child for node_id in [node.id for node in self.nodes]]
        )
        self.assertEqual(x_s.get().tolist(), x.tolist())

    def test_add_shared_tensors(self):
        x = th.tensor([1, 2, 3, 4])
        y = th.tensor([4, 5, 6, 7])
        result = x + y

        x_s = x.share(*self.nodes)
        y_s = y.share(*self.nodes)

        result_s = x_s + y_s
        self.assertEqual(result_s.get().tolist(), result.tolist())

    def test_sub_shared_tensors(self):
        x = th.tensor([1, 2, 3, 4, 5])
        y = th.tensor([4, 5, 6, 7, 8])

        result = x - y

        x_s = x.share(*self.nodes)
        y_s = y.share(*self.nodes)

        result_s = x_s - y_s
        self.assertEqual(result_s.get().tolist(), result.tolist())

    def test_mul_shared_tensors(self):
        x = th.tensor([[1], [2], [3], [15], [50]])

        y = th.tensor([5])

        result = x.matmul(y.t())

        x_s = x.share(self.nodes[0], self.nodes[1], crypto_provider=self.nodes[2])
        y_s = y.share(self.nodes[0], self.nodes[1], crypto_provider=self.nodes[2])

        result_s = x_s.matmul(y_s.t())
        self.assertEqual(result_s.get().tolist(), result.tolist())


class GridAPITest(unittest.TestCase):
    def setUp(self):
        self.my_grid = gr.GridNetwork(gateway_url)

    def tearDown(self):
        self.my_grid.disconnect_nodes()

    def test_connected_nodes(self):
        response = json.loads(requests.get(gateway_url + "/connected-nodes").content)
        self.assertEqual(len(response["grid-nodes"]), 3)
        self.assertTrue("Bob" in response["grid-nodes"])
        self.assertTrue("Alice" in response["grid-nodes"])
        self.assertTrue("James" in response["grid-nodes"])

    def test_grid_search(self):
        nodes = []
        for (node_id, port) in zip(ids, ports):
            node = gr.WebsocketGridClient(
                hook, "http://localhost:" + port + "/", id=node_id
            )
            node.connect()
            nodes.append(node)

        x = th.tensor([1, 2, 3, 4, 5]).tag("#simple-tensor").describe("Simple tensor")
        y = (
            th.tensor([[4], [5], [7], [8]])
            .tag("#2d-tensor")
            .describe("2d tensor example")
        )
        z = (
            th.tensor([[0, 0, 0, 0, 0]])
            .tag("#zeros-tensor")
            .describe("tensor with zeros")
        )
        w = (
            th.tensor([[0, 0, 0, 0, 0]])
            .tag("#zeros-tensor")
            .describe("tensor with zeros")
        )

        x_s = x.send(nodes[0])
        y_s = y.send(nodes[1])
        z_s = z.send(nodes[2])
        w_s = w.send(nodes[0])

        x_s.child.garbage_collect_data = False
        y_s.child.garbage_collect_data = False
        z_s.child.garbage_collect_data = False
        w_s.child.garbage_collect_data = False

        for node in nodes:
            node.disconnect()

        simple_tensor = self.my_grid.search("#simple-tensor")
        self.assertEqual(len(simple_tensor), 1)
        zeros_tensor = self.my_grid.search("#zeros-tensor")
        self.assertEqual(len(zeros_tensor), 2)
        d_tensor = self.my_grid.search("#2d-tensor")
        self.assertEqual(len(d_tensor), 1)
        nothing = self.my_grid.search("#nothing")
        self.assertEqual(len(nothing), 0)
