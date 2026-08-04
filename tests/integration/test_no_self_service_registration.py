"""Guards the decision that there is no open self-service registration.

The codebase used to carry a `register_user` service function reachable from
no route. It was also broken: it passed `nome_pai`/`nome_mae` to Aluno and
`matricula`/`salario` to Gestor, columns that were dropped by migration, so
any call would have raised TypeError and surfaced as a 500.

Rather than repair a function nobody could call, it was deleted. Accounts are
created either by an authenticated gestor, or through the aluno self-signup
flow that lands in PENDING_SIGNUP and waits for approval. These tests pin that
arrangement down so a future open registration endpoint has to be a deliberate,
visible change rather than an accident.
"""

import pytest


@pytest.mark.integration
def test_no_open_registration_route_is_exposed(app):
    """No route may create an account without going through auth or approval."""
    registration_like = [
        str(rule)
        for rule in app.url_map.iter_rules()
        if "register" in str(rule).lower() or "cadastro" in str(rule).lower()
    ]

    assert registration_like == [], (
        "An open registration route appeared. Account creation must stay behind "
        f"gestor authentication or the PENDING_SIGNUP approval flow. Found: {registration_like}"
    )


@pytest.mark.integration
def test_auth_service_exposes_no_register_user():
    """The deleted dead function must not quietly come back."""
    from app.services import auth_service

    assert not hasattr(auth_service, "register_user"), (
        "register_user was deleted because it was unreachable and passed columns "
        "that no longer exist on Aluno/Gestor. If account creation is being added "
        "back, route it and cover it with tests."
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    "url",
    ["/v1/users/alunos", "/v1/users/motoristas"],
)
def test_account_creation_requires_authentication(client, url):
    """The real creation endpoints reject anonymous callers before touching the DB."""
    response = client.post(
        url,
        json={"nome": "Alguem", "email": "alguem@example.com", "cpf": "12345678909"},
    )

    assert response.status_code == 401, (
        f"{url} answered {response.status_code} to an anonymous account creation "
        "attempt; it must require a gestor token."
    )
