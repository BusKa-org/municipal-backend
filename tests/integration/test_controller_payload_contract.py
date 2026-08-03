"""Characterization tests for two repeated controller patterns.

These tests describe what the controllers do TODAY, not what they should do.
They exist to lock the observable HTTP contract in place before the
`request.get_json(silent=True) or {}` and `{"items": xs, "total": len(xs)}`
duplication is factored into shared helpers.

Two properties are pinned:

1. Envelope: list endpoints answer with exactly the keys ``items`` and
   ``total``, where ``total`` equals the number of returned items.

2. Payload fallback: an absent body, a malformed JSON body and an explicit
   empty object are indistinguishable to the endpoint -- all three collapse to
   ``{}`` and therefore produce byte-identical responses.
"""

import pytest

from tests.helpers.assertions import assert_json_ok

# --------------------------------------------------------------------------
# 1. Envelope shape: {"items": [...], "total": N}
# --------------------------------------------------------------------------

# (url, name of the fixture supplying the acting user)
ENVELOPE_ROUTES = [
    ("/v1/users", "gestor"),
    ("/v1/users/motoristas", "gestor"),
    ("/v1/instituicoes/", "gestor"),
    ("/v1/onibus/", "gestor"),
    ("/v1/pontos/", "gestor"),
    ("/v1/alunos/", "gestor"),
    ("/v1/rotas/", "gestor"),
    ("/v1/viagens/", "gestor"),
    ("/v1/rotas/me", "aluno"),
    ("/v1/viagens/aluno/agenda", "aluno"),
    ("/v1/viagens/minhas", "motorista"),
]


@pytest.mark.integration
@pytest.mark.parametrize(("url", "actor_name"), ENVELOPE_ROUTES)
def test_list_envelope_shape(request, url, actor_name):
    """items/total envelope, with total consistent with the item count."""
    actor = request.getfixturevalue(actor_name)

    r = actor.client.get(url)

    assert r.status_code == 200, r.get_data(as_text=True)
    data = assert_json_ok(r)

    assert set(data.keys()) == {"items", "total"}, f"{url} -> {sorted(data.keys())}"
    assert isinstance(data["items"], list), f"{url} items is {type(data['items'])}"
    assert isinstance(data["total"], int), f"{url} total is {type(data['total'])}"
    assert data["total"] == len(data["items"]), f"{url} total disagrees with items"


@pytest.mark.integration
def test_public_instituicoes_envelope_shape(client):
    """The unauthenticated listing carries the same envelope."""
    r = client.get("/v1/instituicoes/public")

    assert r.status_code == 200, r.get_data(as_text=True)
    data = assert_json_ok(r)

    assert set(data.keys()) == {"items", "total"}
    assert data["total"] == len(data["items"])


@pytest.mark.integration
def test_envelope_total_tracks_real_rows(gestor, ponto, onibus):
    """total is derived from the rows, not a hardcoded value."""
    pontos = assert_json_ok(gestor.client.get("/v1/pontos/"))
    onibus_data = assert_json_ok(gestor.client.get("/v1/onibus/"))

    assert pontos["total"] == len(pontos["items"]) >= 1
    assert onibus_data["total"] == len(onibus_data["items"]) >= 1


# --------------------------------------------------------------------------
# 2. Payload fallback: absent == malformed == {}
# --------------------------------------------------------------------------

# (method, url, acting-user fixture or None, status returned for an empty body)
#
# These are the routes where `get_json(silent=True) or {}` is the first gate,
# i.e. they do NOT carry `@api.expect(..., validate=True)`.
#
# Note the odd one out: PATCH /v1/users/me is a partial update, so an empty
# payload is a legitimate no-op that answers 200 with the unchanged profile.
# Every other route treats an empty payload as a validation failure.
PAYLOAD_ROUTES = [
    ("post", "/v1/auth/login", None, 400),
    ("post", "/v1/alunos/signup", None, 400),
    ("post", "/v1/rotas/", "gestor", 400),
    ("post", "/v1/onibus/", "gestor", 400),
    ("post", "/v1/pontos/", "gestor", 400),
    ("post", "/v1/instituicoes/", "gestor", 400),
    ("post", "/v1/users/motoristas", "gestor", 400),
    ("post", "/v1/users/change-password", "gestor", 400),
    ("patch", "/v1/users/me", "gestor", 200),
    ("post", "/v1/viagens/", "gestor", 400),
]


def _caller(request, actor_name, method):
    """Return the bound HTTP method for the acting user (or anonymous)."""
    if actor_name is None:
        return getattr(request.getfixturevalue("client"), method)
    return getattr(request.getfixturevalue(actor_name).client, method)


def _comparable(response):
    """Response body with the per-request correlation id removed.

    Error envelopes carry a fresh ``request_id`` UUID on every call, so raw
    bodies never compare equal. Everything else must match exactly.
    """
    body = response.get_json()
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        error = {k: v for k, v in body["error"].items() if k != "request_id"}
        return {**body, "error": error}
    return body


@pytest.mark.integration
@pytest.mark.parametrize(("method", "url", "actor_name", "empty_status"), PAYLOAD_ROUTES)
def test_absent_malformed_and_empty_bodies_are_equivalent(
    request, method, url, actor_name, empty_status
):
    """No body, unparseable body and {} all collapse to the same response.

    This is the whole observable effect of `get_json(silent=True) or {}`:
    the endpoint never distinguishes "you sent nothing" from "you sent
    garbage" from "you sent an empty object".
    """
    no_body = _caller(request, actor_name, method)(url)
    malformed = _caller(request, actor_name, method)(
        url, data="{this is not json", content_type="application/json"
    )
    empty = _caller(request, actor_name, method)(url, json={})

    assert no_body.status_code == malformed.status_code == empty.status_code, (
        f"{method.upper()} {url}: absent={no_body.status_code} "
        f"malformed={malformed.status_code} empty={empty.status_code}"
    )
    assert _comparable(no_body) == _comparable(malformed) == _comparable(empty), (
        f"{method.upper()} {url}: bodies differ across absent/malformed/empty"
    )


@pytest.mark.integration
@pytest.mark.parametrize(("method", "url", "actor_name", "empty_status"), PAYLOAD_ROUTES)
def test_empty_body_status_is_unchanged(request, method, url, actor_name, empty_status):
    """Exact status code returned for an empty payload, route by route."""
    r = _caller(request, actor_name, method)(url, json={})

    assert r.status_code == empty_status, (
        f"{method.upper()} {url} returned {r.status_code}, expected "
        f"{empty_status}: {r.get_data(as_text=True)[:200]}"
    )
    assert r.is_json, f"{method.upper()} {url} did not answer JSON"


@pytest.mark.integration
@pytest.mark.parametrize(("method", "url", "actor_name", "empty_status"), PAYLOAD_ROUTES)
def test_empty_list_body_falls_back_to_empty_object(
    request, method, url, actor_name, empty_status
):
    """`[] or {}` is falsy, so an empty list behaves exactly like no body.

    Pinned because a helper that only special-cases ``None`` would change this.
    """
    empty_list = _caller(request, actor_name, method)(url, json=[])
    empty_obj = _caller(request, actor_name, method)(url, json={})

    assert empty_list.status_code == empty_obj.status_code, (
        f"{method.upper()} {url}: []={empty_list.status_code} "
        f"vs {{}}={empty_obj.status_code}"
    )
    assert _comparable(empty_list) == _comparable(empty_obj)


@pytest.mark.integration
@pytest.mark.parametrize(("method", "url", "actor_name", "empty_status"), PAYLOAD_ROUTES)
def test_non_empty_list_body_is_forwarded_verbatim(
    request, method, url, actor_name, empty_status
):
    """A non-empty list is truthy, so it reaches the schema as a list.

    Today this surfaces as a client error rather than a crash. Pinned because
    a helper coercing non-dicts to ``{}`` would quietly alter this path.
    """
    r = _caller(request, actor_name, method)(url, json=[{"a": 1}])

    assert 400 <= r.status_code < 500, (
        f"{method.upper()} {url} returned {r.status_code} for a list body: "
        f"{r.get_data(as_text=True)[:200]}"
    )
    assert r.is_json


# --------------------------------------------------------------------------
# 3. Routes fronted by flask-restx `validate=True`
# --------------------------------------------------------------------------
#
# POST /v1/ocorrencias/ is declared `@api.expect(_ocorrencia_input,
# validate=True)`. flask-restx validates the payload *before* the handler
# runs, using a non-silent `request.get_json()`. A request with no JSON
# content type is therefore rejected with 415 and the handler's
# `silent=True` fallback is never reached.
#
# This is why the route is excluded from the equivalence table above, and it
# is the behaviour most at risk of drifting if the fallback is refactored
# without noticing the extra gate.


@pytest.mark.integration
def test_restx_validated_route_rejects_absent_body_with_415(aluno):
    """No content type is refused by flask-restx before the handler runs."""
    r = aluno.client.post("/v1/ocorrencias/")

    assert r.status_code == 415, r.get_data(as_text=True)


@pytest.mark.integration
def test_restx_validated_route_rejects_empty_object_with_400(aluno):
    """A well-formed but empty JSON object fails model validation."""
    r = aluno.client.post("/v1/ocorrencias/", json={})

    assert r.status_code == 400, r.get_data(as_text=True)
    assert r.is_json


@pytest.mark.integration
def test_restx_validated_route_rejects_malformed_body_with_400(aluno):
    """Unparseable JSON with a JSON content type is a 400, not a 415."""
    r = aluno.client.post(
        "/v1/ocorrencias/", data="{this is not json", content_type="application/json"
    )

    assert r.status_code == 400, r.get_data(as_text=True)
