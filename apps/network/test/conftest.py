import pytest
import os
from gridnetwork import create_app


@pytest.fixture(scope="session")
def app():
    BASEDIR = os.path.dirname(os.path.dirname(__file__))
    db_path = "sqlite:///" + BASEDIR + "/databaseGridNetwork.db"

    yield create_app(debug=True, db_config={"SQLALCHEMY_DATABASE_URI": db_path})

    os.remove(BASEDIR + "/databaseGridNetwork.db")


@pytest.fixture
def client(app):
    return app.test_client()
