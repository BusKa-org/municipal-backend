import pytest


@pytest.mark.integration
def test_users_requires_auth(client):
    r = client.get("/v1/users")
    assert r.status_code in (401, 422)


@pytest.mark.integration
def test_users_with_auth(gestor):
    r = gestor.client.get("/v1/users")
    assert r.status_code == 200, r.get_data(as_text=True)
    assert r.is_json
    data = r.get_json()
    assert isinstance(data, list)
    assert any(u.get("id") == str(gestor.user.id) for u in data)
