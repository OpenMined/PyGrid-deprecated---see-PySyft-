import unittest
import time
import pytest
from random import randint, sample

import grid as gr
import syft as sy
import torch as th
import torch.nn.functional as F
import numpy as np

from test import PORTS, IDS

hook = sy.TorchHook(th)


def test_host_plan_model(connected_node):
    class Net(sy.Plan):
        def __init__(self):
            super(Net, self).__init__()
            self.fc1 = th.nn.Linear(2, 1)
            self.bias = th.tensor([1000.0])
            self.state += ["fc1", "bias"]

        def forward(self, x):
            x = self.fc1(x)
            return F.log_softmax(x, dim=0) + self.bias

    model = Net()
    model.build(th.tensor([1.0, 2]))

    nodes = list(connected_node.values())
    bob = nodes[0]
    bob.serve_model(model, model_id="1")

    # Call one time
    prediction = bob.run_inference(model_id="1", data=th.tensor([1.0, 2]))["prediction"]
    assert th.tensor(prediction) == th.tensor([1000.0])

    # Call one more time
    prediction = bob.run_inference(model_id="1", data=th.tensor([1.0, 2]))["prediction"]
    assert th.tensor(prediction) == th.tensor([1000.0])


def test_host_models_with_the_same_key(connected_node):
    class Net(sy.Plan):
        def __init__(self):
            super(Net, self).__init__()
            self.fc1 = th.nn.Linear(2, 1)
            self.bias = th.tensor([1000.0])
            self.state += ["fc1", "bias"]

        def forward(self, x):
            x = self.fc1(x)
            return F.log_softmax(x, dim=1) + self.bias

    model = Net()
    model.build(th.tensor([1.0, 2]))

    nodes = list(connected_node.values())
    bob = nodes[0]

    # Serve it once with no problems
    assert "success" in bob.serve_model(model, model_id="2")
    # Error when using the same id twice
    assert "error" in bob.serve_model(model, model_id="2")


@pytest.mark.skipif(
    th.__version__ >= "1.1",
    reason="bug in pytorch version 1.1.0, jit.trace returns raw C function",
)
def test_host_jit_model(connected_node):
    class Net(th.nn.Module):
        def __init__(self):
            super(Net, self).__init__()
            self.fc1 = th.nn.Linear(2, 1)
            self.bias = th.tensor([1000.0])

        def forward(self, x):
            x = self.fc1(x)
            return F.log_softmax(x, dim=1) + self.bias

    model = Net()
    trace_model = th.jit.trace(model, th.tensor([1.0, 2]))

    nodes = list(connected_node.values())
    bob = nodes[0]
    bob.serve_model(trace_model, model_id="1")

    # Call one time
    prediction = bob.run_inference(model_id="1", data=th.tensor([1.0, 2]))["prediction"]
    assert th.tensor(prediction) == th.tensor([1000.0])

    # Call one more time
    prediction = bob.run_inference(model_id="1", data=th.tensor([1.0, 2]))["prediction"]
    assert th.tensor(prediction) == th.tensor([1000.0])


@pytest.mark.parametrize(
    "test_input, expected", [(node_id, node_id) for node_id in IDS]
)
def test_connect_nodes(test_input, expected, connected_node):
    assert connected_node[test_input].id == expected


def test_connect_nodes(connected_node):
    try:
        for node in connected_node:
            for n in connected_node:
                if n == node:
                    continue
                else:
                    connected_node[node].connect_grid_node(
                        connected_node[n].uri, connected_node[n].id
                    )
    except:
        unittest.TestCase.fail("test_connect_nodes : Exception raised!")


@pytest.mark.parametrize(
    "node_id, tensor,time_interval",
    list(map(lambda x: (x, np.random.rand(3, 2), 0.5), IDS)),
)
def test_send_tensor(node_id, tensor, time_interval, connected_node):
    x = th.tensor(tensor)
    x_s = x.send(connected_node[node_id])

    assert x_s.location.id == node_id
    assert x_s.get().tolist() == x.tolist()
    time.sleep(time_interval)


@pytest.mark.parametrize(
    "node_id, tensor,tag, time_interval",
    list(
        map(
            lambda x, y: (x, np.random.rand(3, 2), y, 0.5),
            IDS,
            ["#first", "#second", "#third"],
        )
    ),
)
def test_send_tag_tensor(node_id, tensor, tag, time_interval, connected_node):
    x = th.tensor(tensor).tag(tag).describe(tag + " description")

    x_s = x.send(connected_node[node_id])
    x_s.child.garbage_collect_data = False

    assert x_s.description == (tag + " description")
    time.sleep(time_interval)


@pytest.mark.parametrize(
    "node_id, tensor, dest,time_interval",
    list(map(lambda x, y: (x, np.random.rand(3, 2), y, 0.5), IDS, IDS[::-1])),
)
def test_move_tensor(node_id, tensor, dest, time_interval, connected_node):
    x = th.tensor(tensor)
    x_s = x.send(connected_node[node_id])
    assert x_s.location.id == node_id

    if node_id != dest:
        x1_s = x_s.move(connected_node[dest])
        assert x1_s.location.id == dest
    time.sleep(time_interval)


@pytest.mark.parametrize(
    "node_id, x_value, y_value,time_interval",
    list(map(lambda x: (x, np.random.rand(3, 2), np.random.rand(3, 2), 0.5), IDS)),
)
def test_add_remote_tensors(node_id, x_value, y_value, time_interval, connected_node):
    x = th.tensor(x_value)
    y = th.tensor(y_value)
    result = x + y

    x_s = x.send(connected_node[node_id])
    y_s = y.send(connected_node[node_id])

    result_s = x_s + y_s
    assert result_s.get().tolist() == result.tolist()
    time.sleep(time_interval)


@pytest.mark.parametrize(
    "node_id, x_value, y_value, time_interval",
    list(map(lambda x: (x, np.random.rand(3, 2), np.random.rand(3, 2), 0.5), IDS)),
)
def test_sub_remote_tensors(node_id, x_value, y_value, time_interval, connected_node):
    x = th.tensor(x_value)
    y = th.tensor(y_value)
    result = x - y

    x_s = x.send(connected_node[node_id])
    y_s = y.send(connected_node[node_id])

    result_s = x_s - y_s
    assert result_s.get().tolist() == result.tolist()
    time.sleep(time_interval)


@pytest.mark.parametrize(
    "node_id, x_value, y_value, time_interval",
    list(map(lambda x: (x, np.random.rand(3, 2), np.random.rand(3, 2), 0.5), IDS)),
)
def test_mul_remote_tensors(node_id, x_value, y_value, time_interval, connected_node):
    x = th.tensor(x_value)
    y = th.tensor(y_value)
    result = x * y

    x_s = x.send(connected_node[node_id])
    y_s = y.send(connected_node[node_id])

    result_s = x_s * y_s
    assert result_s.get().tolist() == result.tolist()
    time.sleep(time_interval)


@pytest.mark.parametrize(
    "node_id, x_value, y_value, time_interval",
    list(map(lambda x: (x, np.random.rand(3, 2), np.random.rand(3, 2), 0.5), IDS)),
)
def test_div_remote_tensors(node_id, x_value, y_value, time_interval, connected_node):
    x = th.tensor(x_value)
    y = th.tensor(y_value)
    result = x / y

    x_s = x.send(connected_node[node_id])
    y_s = y.send(connected_node[node_id])

    result_s = x_s / y_s
    assert result_s.get().tolist() == result.tolist()
    time.sleep(time_interval)


@pytest.mark.parametrize(
    "node_id, x_value, y_value, time_interval",
    list(map(lambda x: (x, np.random.rand(3, 2), randint(0, 10), 0.5), IDS)),
)
def test_exp_remote_tensor(node_id, x_value, y_value, time_interval, connected_node):
    x = th.tensor(x_value)
    result = x ** y_value

    x_s = x.send(connected_node[node_id])
    result_s = x_s ** y_value
    assert result_s.get().tolist() == result.tolist()
    time.sleep(time_interval)


@pytest.mark.parametrize("node_id", IDS)
def test_share_tensors(node_id, connected_node):
    x = th.tensor([1, 2, 3, 4, 5, 6])
    x_s = x.share(*connected_node.values())
    assert node_id in x_s.child.child
    assert x_s.get().tolist() == x.tolist()


@pytest.mark.parametrize(
    "x_value, y_value, time_interval",
    [
        (sample(range(i + 1), i + 1), sample(range(i + 1), i + 1), 0.5)
        for i in range(10)
    ],
)
def test_add_shared_tensors(x_value, y_value, time_interval, connected_node):
    x = th.tensor(x_value)
    y = th.tensor(y_value)
    result = x + y

    x_s = x.share(*connected_node.values())
    y_s = y.share(*connected_node.values())

    result_s = x_s + y_s
    assert result_s.get().tolist() == result.tolist()
    time.sleep(time_interval)


@pytest.mark.parametrize(
    "x_value, y_value, time_interval",
    [
        (sample(range(i + 1), i + 1), sample(range(i + 1), i + 1), 0.5)
        for i in range(10)
    ],
)
def test_sub_shared_tensors(x_value, y_value, time_interval, connected_node):
    x = th.tensor([1, 2, 3, 4])
    y = th.tensor([5, 6, 7, 8])
    result = x - y

    x_s = x.share(*connected_node.values())
    y_s = y.share(*connected_node.values())

    result_s = x_s - y_s
    assert result_s.get().tolist() == result.tolist()
    time.sleep(time_interval)


@pytest.mark.parametrize(
    "x_value, y_value,time_interval",
    [
        (np.random.randint(100, size=(5, x)), np.random.randint(10, size=(x, 1)), 0.5)
        for x in range(10)
    ],
)
def test_mul_shared_tensors(x_value, y_value, time_interval, connected_node):
    x = th.tensor(x_value)
    y = th.tensor(y_value)

    result = x.matmul(y)

    nodes = list(connected_node.values())

    bob = nodes[0]
    alice = nodes[1]
    james = nodes[2]

    x_s = x.share(bob, alice, crypto_provider=james)
    y_s = y.share(bob, alice, crypto_provider=james)

    result_s = x_s.matmul(y_s)
    assert result_s.get().tolist() == result.tolist()
    time.sleep(time_interval)
