import pytest

def test_empty_db(client):
    """Start with a blank database."""

    rv = client.get('/')
    assert b'Howdy' in rv.data
