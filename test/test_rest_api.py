import pytest
import binascii
import syft as sy
from syft import codes

import torch as th
from grid.app.models import Worker as WorkerMDL
from grid.app.models import WorkerObject


def test_empty_db(client):
    """Start with a blank database."""

    rv = client.get('/')
    assert b'Howdy World' in rv.data


def test_identity(client):
    rv = client.get('/identity/')
    assert b'OpenGrid' in rv.data


def test_create_worker(client):
    x = th.tensor([1,2,3,4])
    msg_type = codes.MSGTYPE.OBJ
    message = (msg_type, x)
    bin_message = sy.serde.serialize(message)
    bin_message = str(binascii.hexlify(bin_message))
    rv = client.post("/cmd/", data={"message": bin_message})

    worker_mdl = WorkerMDL.query.filter_by(public_id='worker').first()
    assert worker_mdl.worker_objects[0].object.sum() == x.sum()
