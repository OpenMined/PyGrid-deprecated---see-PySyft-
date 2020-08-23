import pytest
from json import loads

from src.app.main.core.exceptions import PyGridError
from src.app.main.routes.roles import model_to_json
from src.app.main.users import Role, User

payload = (
    '{"name": "mario mario", "can_triage_jobs": false,'
    '"can_edit_settings": false, "can_create_users": true,'
    '"can_create_groups": true, "can_edit_roles": false,'
    '"can_manage_infrastructure": false}'
)

JSON_DECODE_ERR_MSG = (
    "Expecting property name enclosed in " "double quotes: line 1 column 2 (char 1)"
)


@pytest.fixture
def cleanup(database):
    yield
    try:
        database.session.query(User).delete()
        database.session.query(Role).delete()
        database.session.commit()
    except:
        database.session.rollback()


# POST ROLE


def test_post_role_missing_key(client):
    result = client.post("/roles", data=payload, content_type="application/json")
    assert result.status_code == 400
    assert result.get_json()["error"] == "Missing request key!"


def test_post_role_bad_data(client):
    result = client.post("/roles", data="{bad", content_type="application/json")
    assert result.status_code == 400
    assert result.get_json()["error"] == JSON_DECODE_ERR_MSG


def test_post_role_missing_user(client):

    headers = {"private-key": "IdoNotExist"}
    result = client.post(
        "/roles", data=payload, content_type="application/json", headers=headers
    )
    assert result.status_code == 404
    assert result.get_json()["error"] == "User ID not found!"


def test_post_role_missing_role(client, database, cleanup):

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=1,
    )

    database.session.add(new_user)
    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.post(
        "/roles", data=payload, content_type="application/json", headers=headers
    )

    assert result.status_code == 404
    assert result.get_json()["error"] == "Role ID not found!"


def test_post_role_unauthorized_user(client, database, cleanup):
    new_role = Role(
        name="Administrator",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=1,
    )

    database.session.add(new_role)
    database.session.add(new_user)
    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.post(
        "/roles", data=payload, content_type="application/json", headers=headers
    )

    assert result.status_code == 403
    assert result.get_json()["error"] == "User is not authorized for this operation!"


def test_post_role_success(client, database, cleanup):
    new_role = Role(
        name="Administrator",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )
    database.session.add(new_role)

    new_role = Role(
        name="Owner",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=True,
        can_manage_infrastructure=True,
    )
    database.session.add(new_role)

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=2,
    )
    database.session.add(new_user)

    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.post(
        "/roles", data=payload, content_type="application/json", headers=headers
    )

    expected_role = loads(payload)
    expected_role["id"] = 3  # Two roles already inserted

    assert result.status_code == 200
    assert result.get_json()["role"] == expected_role


# GET ALL ROLES


def test_get_all_roles_missing_key(client):
    result = client.get("/roles", data=payload, content_type="application/json")
    assert result.status_code == 400
    assert result.get_json()["error"] == "Missing request key!"


def test_get_all_roles_missing_user(client):

    headers = {"private-key": "IdoNotExist"}
    result = client.get("/roles", content_type="application/json", headers=headers)
    assert result.status_code == 404
    assert result.get_json()["error"] == "User ID not found!"


def test_get_all_roles_missing_role(client, database, cleanup):

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=1,
    )

    database.session.add(new_user)
    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.get("/roles", content_type="application/json", headers=headers)

    assert result.status_code == 404
    assert result.get_json()["error"] == "Role ID not found!"


def test_get_all_roles_unauthorized_user(client, database, cleanup):
    new_role = Role(
        name="User",
        can_triage_jobs=False,
        can_edit_settings=False,
        can_create_users=False,
        can_create_groups=False,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=1,
    )

    database.session.add(new_role)
    database.session.add(new_user)
    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.get("/roles", content_type="application/json", headers=headers)

    assert result.status_code == 403
    assert result.get_json()["error"] == "User is not authorized for this operation!"


def test_get_all_roles_success(client, database, cleanup):
    role1 = Role(
        name="User",
        can_triage_jobs=False,
        can_edit_settings=False,
        can_create_users=False,
        can_create_groups=False,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )
    database.session.add(role1)

    role2 = Role(
        name="Administrator",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )
    database.session.add(role2)

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=2,
    )
    database.session.add(new_user)

    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.get("/roles", content_type="application/json", headers=headers)

    expected_roles = [model_to_json(role1), model_to_json(role2)]

    assert result.status_code == 200
    assert result.get_json()["roles"] == expected_roles


# GET SINGLE ROLE


def test_get_role_missing_key(client):
    result = client.get("/roles/1", data=payload, content_type="application/json")
    assert result.status_code == 400
    assert result.get_json()["error"] == "Missing request key!"


def test_get_role_missing_user(client):

    headers = {"private-key": "IdoNotExist"}
    result = client.get("/roles/2", content_type="application/json", headers=headers)
    assert result.status_code == 404
    assert result.get_json()["error"] == "User ID not found!"


def test_get_role_missing_role(client, database, cleanup):

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=1,
    )

    database.session.add(new_user)
    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.get("/roles/1", content_type="application/json", headers=headers)

    assert result.status_code == 404
    assert result.get_json()["error"] == "Role ID not found!"


def test_get_role_unauthorized_user(client, database, cleanup):
    new_role = Role(
        name="User",
        can_triage_jobs=False,
        can_edit_settings=False,
        can_create_users=False,
        can_create_groups=False,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=1,
    )

    database.session.add(new_role)
    database.session.add(new_user)
    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.get("/roles/1", content_type="application/json", headers=headers)

    assert result.status_code == 403
    assert result.get_json()["error"] == "User is not authorized for this operation!"


def test_get_missing_role(client, database, cleanup):
    new_role = Role(
        name="Compliance Officer",
        can_triage_jobs=True,
        can_edit_settings=False,
        can_create_users=False,
        can_create_groups=False,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=1,
    )

    database.session.add(new_role)
    database.session.add(new_user)
    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.get("/roles/2", content_type="application/json", headers=headers)

    assert result.status_code == 404
    assert result.get_json()["error"] == "Role ID not found!"


def test_get_role_success(client, database, cleanup):
    role1 = Role(
        name="User",
        can_triage_jobs=False,
        can_edit_settings=False,
        can_create_users=False,
        can_create_groups=False,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )
    database.session.add(role1)

    role2 = Role(
        name="Administrator",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )
    database.session.add(role2)

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=2,
    )
    database.session.add(new_user)

    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.get("/roles/1", content_type="application/json", headers=headers)

    expected_role = model_to_json(role1)

    assert result.status_code == 200
    assert result.get_json()["role"] == expected_role


# PUT ROLE


def test_put_role_missing_key(client):
    result = client.put("/roles/1", data=payload, content_type="application/json")
    assert result.status_code == 400
    assert result.get_json()["error"] == "Missing request key!"


def test_put_role_bad_data(client):
    result = client.put("/roles/2", data="{bad", content_type="application/json")
    assert result.status_code == 400
    assert result.get_json()["error"] == JSON_DECODE_ERR_MSG


def test_put_role_missing_user(client):

    headers = {"private-key": "IdoNotExist"}
    result = client.put(
        "/roles/1", data=payload, content_type="application/json", headers=headers
    )
    assert result.status_code == 404
    assert result.get_json()["error"] == "User ID not found!"


def test_put_role_missing_role(client, database, cleanup):

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=1,
    )

    database.session.add(new_user)
    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.put(
        "/roles/1", data=payload, content_type="application/json", headers=headers
    )

    assert result.status_code == 404
    assert result.get_json()["error"] == "Role ID not found!"


def test_put_role_unauthorized_user(client, database, cleanup):
    new_role = Role(
        name="Administrator",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=1,
    )

    database.session.add(new_role)
    database.session.add(new_user)
    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.put(
        "/roles/1", data=payload, content_type="application/json", headers=headers
    )

    assert result.status_code == 403
    assert result.get_json()["error"] == "User is not authorized for this operation!"


def test_put_over_missing_role(client, database, cleanup):
    new_role = Role(
        name="Administrator",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )
    database.session.add(new_role)

    new_role = Role(
        name="Owner",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=True,
        can_manage_infrastructure=True,
    )
    database.session.add(new_role)

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=2,
    )
    database.session.add(new_user)

    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.put(
        "/roles/3", data=payload, content_type="application/json", headers=headers
    )

    assert result.status_code == 404
    assert result.get_json()["error"] == "Role ID not found!"


def test_put_role_success(client, database, cleanup):
    new_role = Role(
        name="Administrator",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )
    database.session.add(new_role)

    new_role = Role(
        name="Owner",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=True,
        can_manage_infrastructure=True,
    )
    database.session.add(new_role)

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=2,
    )
    database.session.add(new_user)

    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.put(
        "/roles/1", data=payload, content_type="application/json", headers=headers
    )

    expected_role = loads(payload)
    expected_role["id"] = 1

    assert result.status_code == 200
    assert result.get_json()["role"] == expected_role


# DELETE ROLE


def test_delete_role_missing_key(client):
    result = client.delete("/roles/1", content_type="application/json")
    assert result.status_code == 400
    assert result.get_json()["error"] == "Missing request key!"


def test_delete_role_missing_user(client):

    headers = {"private-key": "IdoNotExist"}
    result = client.delete("/roles/1", headers=headers, content_type="application/json")
    assert result.status_code == 404
    assert result.get_json()["error"] == "User ID not found!"


def test_delete_role_missing_role(client, database, cleanup):

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=1,
    )

    database.session.add(new_user)
    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.delete("/roles/1", headers=headers, content_type="application/json")

    assert result.status_code == 404
    assert result.get_json()["error"] == "Role ID not found!"


def test_delete_role_unauthorized_user(client, database, cleanup):
    new_role = Role(
        name="Administrator",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=1,
    )

    database.session.add(new_role)
    database.session.add(new_user)
    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.delete("/roles/1", headers=headers, content_type="application/json")

    assert result.status_code == 403
    assert result.get_json()["error"] == "User is not authorized for this operation!"


def test_delete_missing_role(client, database, cleanup):
    new_role = Role(
        name="Administrator",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )
    database.session.add(new_role)

    new_role = Role(
        name="Owner",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=True,
        can_manage_infrastructure=True,
    )
    database.session.add(new_role)

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=2,
    )
    database.session.add(new_user)

    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.delete("/roles/3", headers=headers, content_type="application/json")

    assert result.status_code == 404
    assert result.get_json()["error"] == "Role ID not found!"


def test_delete_role_success(client, database, cleanup):
    new_role = Role(
        name="Administrator",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=False,
        can_manage_infrastructure=False,
    )
    database.session.add(new_role)

    new_role = Role(
        name="Owner",
        can_triage_jobs=True,
        can_edit_settings=True,
        can_create_users=True,
        can_create_groups=True,
        can_edit_roles=True,
        can_manage_infrastructure=True,
    )
    database.session.add(new_role)

    new_user = User(
        email="tech@gibberish.com",
        hashed_password="BDEB6E8EE39B6C70835993486C9E65DC",
        salt="]GBF[R>GX[9Cmk@DthFT!mhloUc%[f",
        private_key="3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb",
        role=2,
    )
    database.session.add(new_user)

    database.session.commit()

    headers = {
        "private-key": "3c777d6e1cece1e78aa9c26ae7fa2ecf33a6d3fb1db7c1313e7b79ef3ee884eb"
    }
    result = client.delete("/roles/1", headers=headers, content_type="application/json")

    assert result.status_code == 200
    assert database.session.query(Role).get(1) is None
