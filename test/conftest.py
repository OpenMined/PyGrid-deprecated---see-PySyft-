import pytest
import torch
from multiprocessing import Process
from grid.app import create_app
from grid.app.config import db
import os
import tempfile


import syft
from syft import TorchHook


def init_db():
    pass
    #db.create_all()

@pytest.fixture()
def start_proc():  # pragma: no cover
    """ helper function for spinning up a websocket participant """

    def _start_proc(participant, kwargs):
        def target():
            server = participant(**kwargs)
            server.start()

        p = Process(target=target)
        p.start()
        return p

    return _start_proc


@pytest.fixture(scope="session", autouse=True)
def hook():
    hook = TorchHook(torch)
    return hook



@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # create a temporary file to isolate the database for each test
#    db_fd, db_path = tempfile.mkstemp()
    # create the app with common test config
    app = create_app({
        'TESTING': True,
        'DATABASE': "sqlite:///:memory:"
    })

    # create the database and load test data
#    with app.app_context():
#        init_db()

    yield app

    # close and remove the temporary database
#    os.close(db_fd)
#    os.unlink(db_path)



@pytest.fixture
def client(app):
    return app.test_client()
