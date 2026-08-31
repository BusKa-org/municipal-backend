"""Filtro ?status= das listagens do gestor (alunos e ocorrências).

Os dois serviços faziam `Enum[status]` dentro de um `try/except KeyError: pass`.
Quando o gestor mandava um status inválido (typo, lowercase, valor de outra
enum) o filtro era descartado em silêncio e a query voltava **tudo** com 200. O
gestor via uma tela que dizia "pendentes de aprovação" listando gente já ativa,
sem nenhum sinal de erro. Agora vira 400 VALIDATION_ERROR nos dois.
"""

import pytest

from app.models.enum import StatusOcorrencia, TipoOcorrencia, UserStatus
from app.models.ocorrencia import Ocorrencia


@pytest.mark.integration
def test_status_invalido_devolve_400_e_nao_lista_todo_mundo(gestor, aluno, aluno_pending, _db):
    """O erro precisa ser explícito — não pode cair para "sem filtro"."""
    aluno.user.status = UserStatus.ACTIVE
    _db.session.commit()

    r = gestor.client.get("/v1/alunos/?status=pending_approval")

    assert r.status_code == 400, r.get_data(as_text=True)

    body = r.get_json() or {}
    assert body["error"]["code"] == "VALIDATION_ERROR"
    # o vazamento antigo: responder 200 com a lista inteira
    assert "items" not in body, "filtro inválido não pode devolver a lista sem filtro"


@pytest.mark.integration
def test_status_valido_continua_filtrando(gestor, aluno, aluno_pending, _db):
    """Guarda contra corrigir demais e passar a rejeitar status legítimo."""
    aluno.user.status = UserStatus.ACTIVE
    _db.session.commit()

    r = gestor.client.get("/v1/alunos/?status=ACTIVE")

    assert r.status_code == 200, r.get_data(as_text=True)

    body = r.get_json() or {}
    ids = {item["id"] for item in body["items"]}
    assert ids == {str(aluno.user.id)}, "deveria trazer só o aluno ACTIVE"


@pytest.mark.integration
def test_sem_status_lista_todos(gestor, aluno, aluno_pending):
    """Sem filtro continua listando a prefeitura inteira."""
    r = gestor.client.get("/v1/alunos/")

    assert r.status_code == 200, r.get_data(as_text=True)

    body = r.get_json() or {}
    ids = {item["id"] for item in body["items"]}
    assert {str(aluno.user.id), str(aluno_pending.user.id)} <= ids


@pytest.fixture()
def ocorrencias(_db, aluno):
    """Uma ocorrência aberta e uma resolvida, ambas da prefeitura do gestor."""
    aberta = Ocorrencia(
        autor_id=aluno.user.id,
        tipo=TipoOcorrencia.ATRASO,
        descricao="ônibus atrasou",
        status=StatusOcorrencia.ABERTA,
    )
    resolvida = Ocorrencia(
        autor_id=aluno.user.id,
        tipo=TipoOcorrencia.SUPERLOTACAO,
        descricao="ônibus lotado",
        status=StatusOcorrencia.RESOLVIDA,
    )
    _db.session.add_all([aberta, resolvida])
    _db.session.commit()
    return aberta, resolvida


@pytest.mark.integration
def test_ocorrencia_status_invalido_devolve_400(gestor, ocorrencias):
    """Mesmo bug do lado das ocorrências: filtro inválido não pode virar 'sem filtro'."""
    r = gestor.client.get("/v1/ocorrencias/?status=aberta")

    assert r.status_code == 400, r.get_data(as_text=True)

    body = r.get_json() or {}
    assert body["error"]["code"] == "VALIDATION_ERROR"
    # a listagem devolve uma lista nua — o vazamento antigo era 200 + tudo
    assert not isinstance(body, list)


@pytest.mark.integration
def test_ocorrencia_status_valido_continua_filtrando(gestor, ocorrencias):
    """Guarda contra passar a rejeitar status legítimo."""
    aberta, _resolvida = ocorrencias

    r = gestor.client.get("/v1/ocorrencias/?status=ABERTA")

    assert r.status_code == 200, r.get_data(as_text=True)

    body = r.get_json()
    assert [o["id"] for o in body] == [str(aberta.id)]
