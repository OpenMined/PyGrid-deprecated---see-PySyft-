import papermill as pm
import nbformat
from .. import worker_ports
import pytest
import os

from pathlib import Path

dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
examples_path = dir_path.parent.parent

data_centric_mnist_path = examples_path.joinpath("examples", "data-centric", "mnist")


def test_notebooks_mnist_01():
    """Test if notebook run"""
    notebook_mnist_01 = data_centric_mnist_path.joinpath(
        "01-FL-mnist-populate-a-grid-node.ipynb"
    )
    res = pm.execute_notebook(
        str(notebook_mnist_01),
        "/dev/null",
        dict(alice_port=worker_ports["alice"], bob_port=worker_ports["bob"]),
    )

    assert isinstance(res, nbformat.notebooknode.NotebookNode)


@pytest.mark.skip(reason="notebook not developed")
def test_notebooks_mnist_02():
    notebook_mnist_02 = (
        "../PyGrid/examples/data-centric/mnist/02-FL-mnist-train-model.ipynb"
    )
    res = pm.execute_notebook(
        notebook_mnist_02,
        "/dev/null",
        dict(alice_port=worker_ports["alice"], bob_port=worker_ports["bob"]),
    )

    assert isinstance(res, nbformat.notebooknode.NotebookNode)
