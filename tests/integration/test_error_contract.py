import pytest


@pytest.mark.integration
def test_error_contract_validation(client):
    r = client.post("/v1/auth/login", json={})
    assert r.status_code == 400
    body = r.get_json() or {}

    assert "error" in body
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(body["error"]["message"], str)


@pytest.mark.integration
def test_error_contract_unauthorized(client):
    r = client.get("/v1/users")
    assert r.status_code in (401, 422)
    body = r.get_json() or {}

    assert "error" in body
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert isinstance(body["error"]["message"], str)
