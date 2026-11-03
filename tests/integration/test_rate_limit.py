import uuid

import pytest
from flask import request
from flask_jwt_extended import create_access_token

from app.extensions import (
    _chave_do_cliente,
    _chave_por_email,
    _chave_por_email_ou_token,
    _chave_por_token,
    _hash,
    limiter,
)

LOGIN = "/v1/auth/login"
FORGOT = "/v1/auth/forgot-password"
RESET = "/v1/auth/reset-password"
ME = "/v1/users/me"


@pytest.fixture()
def limitado(app, client, monkeypatch):
    """Suite's app with tiny limits; create_app() cannot run twice (global scheduler)."""
    # The limits are read from app.config on each request, so setitem is enough.
    monkeypatch.setitem(app.config, "RATELIMIT_ENABLED", True)
    monkeypatch.setitem(app.config, "RATELIMIT_DEFAULT", "3 per minute")
    monkeypatch.setitem(app.config, "RATELIMIT_AUTH", "2 per minute")
    monkeypatch.setitem(app.config, "RATELIMIT_SENSITIVE", "1 per minute")
    monkeypatch.setitem(app.config, "RATELIMIT_REALTIME", "2 per minute")
    limiter.reset()
    return client


def _corpo_do_429(r):
    assert r.status_code == 429
    corpo = r.get_json()
    # One shape only: no "message" at the top (flask-restx adds it if allowed).
    assert set(corpo) == {"error"}
    assert corpo["error"]["code"] == "RATE_LIMITED"
    assert corpo["error"]["details"]["limit"]
    assert int(r.headers["Retry-After"]) > 0


@pytest.mark.integration
def test_limite_estourado_devolve_429_no_formato_padrao(limitado):
    assert limitado.post(RESET, json={}).status_code == 400

    _corpo_do_429(limitado.post(RESET, json={}))


@pytest.mark.integration
def test_limite_padrao_devolve_o_mesmo_429(limitado):
    # /v1/users/me has no limit of its own: falls into RATELIMIT_DEFAULT (3 per minute).
    for _ in range(3):
        assert limitado.get(ME).status_code == 401

    _corpo_do_429(limitado.get(ME))


@pytest.mark.integration
def test_login_conta_por_email_e_nao_por_ip(limitado):
    for ip in ("10.0.0.1", "10.0.0.2"):
        limitado.post(
            LOGIN, json={"email": "A@x.com", "password": "e"}, environ_base={"REMOTE_ADDR": ip}
        )
    # Same (normalized) e-mail from a third IP: already over the limit.
    bloqueado = limitado.post(
        LOGIN,
        json={"email": " a@X.com ", "password": "e"},
        environ_base={"REMOTE_ADDR": "10.0.0.3"},
    )
    # Another student behind the same IP (school Wi-Fi) still gets in.
    outro_email = limitado.post(
        LOGIN, json={"email": "b@x.com", "password": "e"}, environ_base={"REMOTE_ADDR": "10.0.0.1"}
    )

    assert bloqueado.status_code == 429
    assert outro_email.status_code != 429


@pytest.mark.integration
def test_consentimento_conta_por_token_e_por_metodo(limitado):
    url = f"/v1/alunos/guardian-consent/{uuid.uuid4()}"
    limitado.get(url)
    limitado.get(url)
    assert limitado.get(url).status_code == 429

    # POST on the same path has its own counter, and so does another token.
    assert limitado.post(url).status_code != 429
    assert limitado.get(f"/v1/alunos/guardian-consent/{uuid.uuid4()}").status_code != 429


@pytest.mark.integration
def test_rotas_diferentes_nao_dividem_contagem(limitado):
    limitado.post(LOGIN, json={})
    limitado.post(LOGIN, json={})
    assert limitado.post(LOGIN, json={}).status_code == 429

    assert limitado.post(FORGOT, json={}).status_code == 400


@pytest.mark.integration
def test_preflight_do_cors_nao_conta(limitado):
    preflight = {
        "Origin": "http://front.example",
        "Access-Control-Request-Method": "GET",
    }
    # /v1/users/me falls into the default limit (3 per minute), checked before the view.
    for _ in range(5):
        assert limitado.options(ME, headers=preflight).status_code == 200

    assert limitado.get(ME).status_code == 401


@pytest.mark.integration
def test_cors_expoe_os_headers_do_limite(limitado):
    r = limitado.post(RESET, json={}, headers={"Origin": "http://front.example"})

    expostos = r.headers["Access-Control-Expose-Headers"]
    for nome in ("Retry-After", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"):
        assert nome in expostos


@pytest.mark.integration
@pytest.mark.parametrize(
    "kwargs",
    [
        {"data": "nao e json", "content_type": "application/json"},
        {"data": "email=a@x.com", "content_type": "text/plain"},
        {"json": ["a@x.com"]},
        {"json": {"email": 123}},
        {"json": {"email": "sem-arroba"}},
        {"json": {"email": "a" * 300 + "@x.com"}},
    ],
)
def test_corpo_sem_email_valido_cai_num_balde_so(app, kwargs):
    with app.test_request_context(LOGIN, method="POST", **kwargs):
        assert _chave_por_email() == "sem-email"


@pytest.mark.integration
def test_chave_do_email_nao_consome_o_corpo(app):
    with app.test_request_context(LOGIN, method="POST", json={"email": " A@X.com "}):
        assert _chave_por_email() == f"email:{_hash('a@x.com')}"
        assert request.get_json() == {"email": " A@X.com "}


@pytest.mark.integration
def test_reset_de_senha_conta_pelo_token_sem_email(app):
    with app.test_request_context(RESET, method="POST", json={"token": "abc", "new_password": "x"}):
        assert _chave_por_email_ou_token() == f"token:{_hash('abc')}"
        assert request.get_json()["new_password"] == "x"


@pytest.mark.integration
def test_reset_de_senha_ignora_token_da_query_string(app):
    with app.test_request_context(f"{RESET}?token=abc", method="POST", json={}):
        assert _chave_por_email_ou_token() == "sem-token"


@pytest.mark.integration
def test_chave_nao_guarda_token_nem_email_em_claro(app):
    token = str(uuid.uuid4())
    url = f"/v1/alunos/guardian-consent/{token}"
    with app.test_request_context(url):
        chave = _chave_por_token()
    with app.test_request_context(url, method="POST"):
        mesma_chave = _chave_por_token()
    with app.test_request_context(f"/v1/alunos/guardian-consent/{uuid.uuid4()}"):
        outra_chave = _chave_por_token()
    assert token not in chave
    assert chave == mesma_chave
    assert chave != outra_chave

    with app.test_request_context(LOGIN, method="POST", json={"email": "a@x.com"}):
        assert "a@x.com" not in _chave_por_email()


@pytest.mark.integration
def test_jwt_invalido_conta_pelo_ip(app):
    with app.test_request_context(
        ME,
        headers={"Authorization": "Bearer nao-e-um-jwt"},
        environ_base={"REMOTE_ADDR": "10.0.0.9"},
    ):
        chave = _chave_do_cliente()
        assert chave == f"ip:{_hash('10.0.0.9')}"
    assert "10.0.0.9" not in chave


@pytest.mark.integration
def test_usuarios_diferentes_nao_dividem_contagem(app, limitado, aluno, other_aluno):
    with app.app_context():
        token_a = create_access_token(identity=str(aluno.user.id))
        token_b = create_access_token(identity=str(other_aluno.user.id))
    url = f"/v1/viagens/{uuid.uuid4()}/localizacao"

    for _ in range(2):
        limitado.get(url, headers={"Authorization": f"Bearer {token_a}"})
    bloqueado = limitado.get(url, headers={"Authorization": f"Bearer {token_a}"})
    outro_usuario = limitado.get(url, headers={"Authorization": f"Bearer {token_b}"})

    assert bloqueado.status_code == 429
    assert outro_usuario.status_code != 429


@pytest.mark.integration
def test_health_e_ready_ficam_fora_do_limite(limitado):
    for _ in range(5):
        assert limitado.get("/health").status_code == 200
        assert limitado.get("/ready").status_code != 429


@pytest.mark.integration
def test_limitador_desligado_na_suite(client):
    for _ in range(5):
        assert client.post(RESET, json={}).status_code == 400
