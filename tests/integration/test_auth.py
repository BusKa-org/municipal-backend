import pytest


@pytest.mark.integration
def test_login_missing_fields_returns_400(client):
    r = client.post("/v1/auth/login", json={})
    assert r.status_code == 400, r.get_data(as_text=True)
    data = r.get_json() or {}
    assert "error" in data


@pytest.mark.integration
def test_login_invalid_credentials_returns_401(client):
    r = client.post("/v1/auth/login", json={"email": "nope@buska.test", "password": "wrong"})
    assert r.status_code == 401, r.get_data(as_text=True)


@pytest.mark.integration
def test_login_success_returns_token(client, gestor):
    r = client.post(
        "/v1/auth/login", json={"email": gestor.user.email, "password": "StrongPass123!"}
    )
    assert r.status_code == 200, r.get_data(as_text=True)
    data = r.get_json() or {}
    assert data.get("token"), f"Token not found in response: {data}"
    assert data.get("user"), f"User not found in response: {data}"
    assert data.get("user").get("id") == str(
        gestor.user.id
    ), f"User ID mismatch: {data.get('user')}"
    assert (
        data.get("user").get("email") == gestor.user.email
    ), f"User email mismatch: {data.get('user')}"
    assert (
        data.get("user").get("nome") == gestor.user.nome
    ), f"User name mismatch: {data.get('user')}"
    assert data["user"]["role"] == gestor.user.role.value, f"User role mismatch: {data.get('user')}"


@pytest.mark.integration
def test_reset_password_get_nao_serve_mais_html(client):
    r = client.get("/v1/auth/reset-password?token=abc")
    assert r.status_code == 405, r.get_data(as_text=True)


@pytest.mark.integration
def test_reset_password_senhas_diferentes_erra_no_confirm_password(client):
    r = client.post(
        "/v1/auth/reset-password",
        json={"token": "abc", "new_password": "NovaSenha123!", "confirm_password": "Outra123!"},
    )
    assert r.status_code == 400, r.get_data(as_text=True)
    details = r.get_json()["error"]["details"]
    assert details == {"confirm_password": ["As senhas não coincidem"]}


@pytest.mark.integration
def test_reset_password_token_invalido_mantem_mensagem_de_link(client):
    r = client.post(
        "/v1/auth/reset-password",
        json={
            "token": "nao-existe",
            "new_password": "NovaSenha123!",
            "confirm_password": "NovaSenha123!",
        },
    )
    assert r.status_code == 400, r.get_data(as_text=True)
    assert r.get_json()["error"]["message"] == "Link inválido ou expirado"
