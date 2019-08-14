import unittest
import grid as gr
import syft as sy
import torch as th
import time
import pytest
from . import PORTS, IDS

hook = sy.TorchHook(th)


class SocketIOTest(unittest.TestCase):
    def setUp(self):
        self.nodes = []
        for (node_id, port) in zip(IDS, PORTS):
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
