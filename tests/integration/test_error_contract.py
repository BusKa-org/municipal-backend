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


@pytest.mark.integration
def test_error_contract_sem_debug_nem_testing(app, client, monkeypatch):
    """O contrato de erro precisa valer em produção, não só com DEBUG ligado.

    O flask_restx trata as exceções levantadas dentro dos Resources com o
    próprio handler, que devolve 500 genérico, e só delega para os
    @app.errorhandler do Flask quando PROPAGATE_EXCEPTIONS é verdadeiro. Esse
    valor cai para DEBUG or TESTING quando não é definido, então o resto da
    suíte nunca exercita o comportamento real de produção: todo erro de
    negócio (400, 401, 403, 404) virava 500 na VM.
    """
    monkeypatch.setitem(app.config, "DEBUG", False)
    monkeypatch.setitem(app.config, "TESTING", False)

    r = client.post("/v1/auth/login", json={"email": "naoexiste@buska.test", "password": "errada"})

    assert r.status_code == 401, "erro de negócio não pode virar 500 em produção"
    assert (r.get_json() or {}).get("error", {}).get("code") == "UNAUTHORIZED"


@pytest.mark.integration
def test_update_me_cadastro_incompleto_devolve_400_e_nao_500(aluno_pending):
    """Erro de negócio levantado dentro do try do service não pode virar 500.

    `update_me()` envolvia o corpo inteiro num `except Exception` que
    reembrulhava qualquer erro como AppError(500) — inclusive o ValidationError
    que o próprio método levanta de propósito quando o cadastro está
    incompleto. O aluno recebia 500 com a mensagem colada dentro de "Erro ao
    atualizar perfil: ..." e sem o details.missing, então o app não tinha como
    dizer quais campos faltavam. O `except AppError: raise` antes do catch-all
    preserva status e payload originais.

    O endereço vai completo de propósito: o que precisa faltar aqui é o
    instituicao_id (AlunoFactory nasce com None), para que o teste falhe pelo
    caminho do guard de cadastro incompleto e não por outro erro qualquer.
    """
    r = aluno_pending.client.put(
        "/v1/alunos/me",
        json={
            "nome": "Aluno Sem Instituição",
            "endereco_casa": {
                "logradouro": "Rua Aprígio Veloso",
                "numero": "882",
                "bairro": "Universitário",
                "cidade": "Campina Grande",
                "cep": "58429-900",
                "latitude": -7.2153,
                "longitude": -35.9089,
            },
        },
    )

    assert r.status_code == 400, r.get_data(as_text=True)

    body = r.get_json() or {}
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "finalizado" in body["error"]["message"]
    assert "instituicao_id" in body["error"]["details"]["missing"]
