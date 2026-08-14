"""Characterization tests for ``app/services/pontos_service.py``.

Purpose: pin the CURRENT observable behaviour of every public function in the
module so the upcoming refactor can be proven behaviour-preserving. These are
deliberately NOT "should" tests: where the behaviour pinned here is a known
bug, the test name and comment say so and point at the REFACTOR_PLAN.md id.
If one of these tests changes in the SAME PR that changes the behaviour of
`pontos_service.py`, the change was not a refactor.
"""

import uuid

import pytest
from sqlalchemy.exc import DataError

from app.core.exceptions import AppError, ForbiddenError, NotFoundError, ValidationError
from app.models.geo import Ponto
from app.services import pontos_service
from app.services.pontos_service import (
    create_ponto,
    delete_ponto,
    get_by_id,
    list_all,
    update_ponto,
)
from tests.factories.geo_factory import PontoFactory

pytestmark = pytest.mark.integration


# ─── helpers ────────────────────────────────────────────────────────────────


def _cria_ponto(_db, prefeitura_id, apelido="Ponto teste"):
    p = PontoFactory(prefeitura_id=prefeitura_id, apelido=apelido, latitude=-7.21, longitude=-35.88)
    _db.session.add(p)
    _db.session.commit()
    return p


# ─── list_all ───────────────────────────────────────────────────────────────


def test_list_all_retorna_pontos_da_prefeitura_do_usuario(_db, gestor, ponto):
    resultado = list_all(str(gestor.user.id))

    assert [p.id for p in resultado] == [ponto.id]


def test_list_all_nao_vaza_pontos_de_outra_prefeitura(_db, gestor, other_prefeitura, ponto):
    alheio = _cria_ponto(_db, other_prefeitura.id, apelido="Ponto alheio")

    resultado = list_all(str(gestor.user.id))

    assert alheio.id not in [p.id for p in resultado]


def test_list_all_nao_exige_papel_aluno_lista(_db, aluno, ponto):
    # Nenhum gate de papel: ALUNO enxerga os pontos da própria prefeitura.
    resultado = list_all(str(aluno.user.id))

    assert [p.id for p in resultado] == [ponto.id]


def test_list_all_usuario_inexistente_404(_db):
    with pytest.raises(NotFoundError) as exc:
        list_all(str(uuid.uuid4()))

    assert str(exc.value) == "Usuário não encontrado"
    assert exc.value.status_code == 404


def test_list_all_nao_valida_formato_de_uuid(_db):
    # CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui)
    # `User.query.get` chama o banco com o texto cru. O Postgres levanta
    # DataError e vira 500 genérico. Deveria virar 404 como qualquer outro
    # usuário inexistente.
    with pytest.raises(DataError):
        list_all("nao-e-uuid")


# ─── get_by_id ──────────────────────────────────────────────────────────────


def test_get_by_id_gestor_recebe_ponto_da_propria_prefeitura(_db, gestor, ponto):
    resultado = get_by_id(str(gestor.user.id), str(ponto.id))

    assert resultado.id == ponto.id


def test_get_by_id_nao_exige_papel_aluno_recebe(_db, aluno, ponto):
    # Nenhum gate de papel na leitura individual.
    resultado = get_by_id(str(aluno.user.id), str(ponto.id))

    assert resultado.id == ponto.id


def test_get_by_id_ponto_de_outra_prefeitura_403(_db, gestor, other_prefeitura):
    alheio = _cria_ponto(_db, other_prefeitura.id)

    with pytest.raises(ForbiddenError) as exc:
        get_by_id(str(gestor.user.id), str(alheio.id))

    assert str(exc.value) == "Acesso negado"
    assert exc.value.status_code == 403


def test_get_by_id_ponto_inexistente_404(_db, gestor):
    with pytest.raises(NotFoundError) as exc:
        get_by_id(str(gestor.user.id), str(uuid.uuid4()))

    assert str(exc.value) == "Ponto não encontrado"
    assert exc.value.status_code == 404


def test_get_by_id_usuario_inexistente_404(_db, ponto):
    with pytest.raises(NotFoundError) as exc:
        get_by_id(str(uuid.uuid4()), str(ponto.id))

    assert str(exc.value) == "Usuário não encontrado"


def test_get_by_id_nao_valida_formato_do_uuid_do_ponto(_db, gestor):
    # CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui): 500 em vez de 404.
    with pytest.raises(DataError):
        get_by_id(str(gestor.user.id), "nao-e-uuid")


# ─── create_ponto ───────────────────────────────────────────────────────────


def test_create_ponto_gestor_persiste_no_banco(_db, gestor):
    novo = create_ponto(
        str(gestor.user.id),
        {"apelido": "Praça Central", "latitude": -7.21, "longitude": -35.88},
    )

    salvo = Ponto.query.get(novo.id)
    assert salvo is not None
    assert salvo.apelido == "Praça Central"
    assert float(salvo.latitude) == -7.21
    assert float(salvo.longitude) == -35.88
    assert salvo.prefeitura_id == gestor.user.prefeitura_id


def test_create_ponto_motorista_tambem_cria(_db, motorista):
    novo = create_ponto(str(motorista.user.id), {"latitude": -7.21, "longitude": -35.88})

    assert Ponto.query.get(novo.id) is not None


def test_create_ponto_aluno_403(_db, aluno):
    with pytest.raises(ForbiddenError) as exc:
        create_ponto(str(aluno.user.id), {"latitude": -7.21, "longitude": -35.88})

    assert str(exc.value) == "Permissão negada"
    assert exc.value.status_code == 403


def test_create_ponto_usuario_inexistente_403_e_nao_404(_db):
    # CARACTERIZAÇÃO DE DIVERGÊNCIA (não corrigida aqui)
    # `list_all` e `get_by_id` devolvem 404 para usuário inexistente. Aqui o
    # `not user` está grudado no teste de papel e o resultado é 403.
    with pytest.raises(ForbiddenError) as exc:
        create_ponto(str(uuid.uuid4()), {"latitude": -7.21, "longitude": -35.88})

    assert str(exc.value) == "Permissão negada"
    assert exc.value.status_code == 403


def test_create_ponto_apelido_ausente_vira_sem_nome(_db, gestor):
    novo = create_ponto(str(gestor.user.id), {"latitude": -7.21, "longitude": -35.88})

    assert novo.apelido == "Sem Nome"


def test_create_ponto_sem_latitude_400(_db, gestor):
    with pytest.raises(ValidationError) as exc:
        create_ponto(str(gestor.user.id), {"longitude": -35.88})

    assert str(exc.value) == "Lat/Lon são obrigatórios"
    assert exc.value.status_code == 400


def test_create_ponto_sem_longitude_400(_db, gestor):
    with pytest.raises(ValidationError) as exc:
        create_ponto(str(gestor.user.id), {"latitude": -7.21})

    assert str(exc.value) == "Lat/Lon são obrigatórios"


def test_create_ponto_coordenada_zero_e_recusada(_db, gestor):
    # CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui)
    # O teste é `not data.get(...)`, então 0 cai junto com None. Latitude 0 é
    # coordenada válida (linha do Equador) e deveria ser aceita.
    with pytest.raises(ValidationError) as exc:
        create_ponto(str(gestor.user.id), {"latitude": 0, "longitude": -35.88})

    assert str(exc.value) == "Lat/Lon são obrigatórios"


def test_create_ponto_ignora_prefeitura_id_do_payload(_db, gestor, other_prefeitura):
    novo = create_ponto(
        str(gestor.user.id),
        {"latitude": -7.21, "longitude": -35.88, "prefeitura_id": str(other_prefeitura.id)},
    )

    assert novo.prefeitura_id == gestor.user.prefeitura_id


def test_create_ponto_erro_de_banco_vaza_sql_na_mensagem(_db, gestor):
    # CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui)
    # O `except Exception` interpola `str(e)` na resposta, então o cliente
    # recebe o SQL, os parâmetros e o nome das colunas dentro de um 500.
    with pytest.raises(AppError) as exc:
        create_ponto(str(gestor.user.id), {"latitude": "abc", "longitude": -35.88})

    assert str(exc.value).startswith("Erro ao criar ponto: ")
    assert "INSERT INTO ponto" in str(exc.value)
    assert exc.value.status_code == 500


# ─── update_ponto ───────────────────────────────────────────────────────────


def test_update_ponto_gestor_altera_campos_simples(_db, gestor, ponto):
    atualizado = update_ponto(
        str(gestor.user.id),
        str(ponto.id),
        {"apelido": "Novo apelido", "latitude": -8.0, "longitude": -36.0},
    )

    assert atualizado.apelido == "Novo apelido"
    assert float(atualizado.latitude) == -8.0
    assert float(atualizado.longitude) == -36.0


def test_update_ponto_campos_ausentes_ficam_inalterados(_db, gestor, ponto):
    apelido_original = ponto.apelido

    atualizado = update_ponto(str(gestor.user.id), str(ponto.id), {"latitude": -8.0})

    assert atualizado.apelido == apelido_original
    assert float(atualizado.latitude) == -8.0


def test_update_ponto_ignora_campos_desconhecidos(_db, gestor, ponto):
    atualizado = update_ponto(
        str(gestor.user.id), str(ponto.id), {"prefeitura_id": str(uuid.uuid4())}
    )

    assert atualizado.prefeitura_id == gestor.user.prefeitura_id


def test_update_ponto_motorista_403_assimetria_com_create(_db, motorista, ponto):
    # CARACTERIZAÇÃO DE DIVERGÊNCIA (não corrigida aqui)
    # MOTORISTA cria ponto mas não edita, e a mensagem de negação é outra.
    with pytest.raises(ForbiddenError) as exc:
        update_ponto(str(motorista.user.id), str(ponto.id), {"apelido": "x"})

    assert str(exc.value) == "Apenas gestores editam pontos"
    assert exc.value.status_code == 403


def test_update_ponto_aluno_403(_db, aluno, ponto):
    with pytest.raises(ForbiddenError) as exc:
        update_ponto(str(aluno.user.id), str(ponto.id), {"apelido": "x"})

    assert str(exc.value) == "Apenas gestores editam pontos"


def test_update_ponto_usuario_inexistente_403_e_nao_404(_db, ponto):
    # CARACTERIZAÇÃO DE DIVERGÊNCIA (não corrigida aqui): mesmo caso do create.
    with pytest.raises(ForbiddenError) as exc:
        update_ponto(str(uuid.uuid4()), str(ponto.id), {"apelido": "x"})

    assert str(exc.value) == "Apenas gestores editam pontos"


def test_update_ponto_inexistente_404(_db, gestor):
    with pytest.raises(NotFoundError) as exc:
        update_ponto(str(gestor.user.id), str(uuid.uuid4()), {"apelido": "x"})

    assert str(exc.value) == "Ponto não encontrado"
    assert exc.value.status_code == 404


def test_update_ponto_de_outra_prefeitura_403(_db, gestor, other_prefeitura):
    alheio = _cria_ponto(_db, other_prefeitura.id)

    with pytest.raises(ForbiddenError) as exc:
        update_ponto(str(gestor.user.id), str(alheio.id), {"apelido": "x"})

    assert str(exc.value) == "Acesso negado"


def test_update_ponto_erro_de_banco_vaza_sql_na_mensagem(_db, gestor, ponto):
    # CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui): mesmo vazamento
    # de `str(e)` do create.
    with pytest.raises(AppError) as exc:
        update_ponto(str(gestor.user.id), str(ponto.id), {"latitude": "abc"})

    assert str(exc.value).startswith("Erro ao atualizar ponto: ")
    assert "UPDATE ponto" in str(exc.value)
    assert exc.value.status_code == 500


# ─── delete_ponto ───────────────────────────────────────────────────────────


def test_delete_ponto_gestor_remove_do_banco(_db, gestor, ponto):
    ponto_id = ponto.id

    assert delete_ponto(str(gestor.user.id), str(ponto_id)) is None
    assert Ponto.query.get(ponto_id) is None


def test_delete_ponto_em_uso_por_rota_400(_db, gestor, ponto, rota_ponto):
    with pytest.raises(AppError) as exc:
        delete_ponto(str(gestor.user.id), str(ponto.id))

    assert str(exc.value) == "Este ponto está sendo usado em uma rota e não pode ser excluído"
    assert exc.value.status_code == 400
    assert Ponto.query.get(ponto.id) is not None


def test_delete_ponto_motorista_403(_db, motorista, ponto):
    with pytest.raises(ForbiddenError) as exc:
        delete_ponto(str(motorista.user.id), str(ponto.id))

    assert str(exc.value) == "Permissão negada"
    assert exc.value.status_code == 403


def test_delete_ponto_aluno_403(_db, aluno, ponto):
    with pytest.raises(ForbiddenError) as exc:
        delete_ponto(str(aluno.user.id), str(ponto.id))

    assert str(exc.value) == "Permissão negada"


def test_delete_ponto_usuario_inexistente_403_e_nao_404(_db, ponto):
    # CARACTERIZAÇÃO DE DIVERGÊNCIA (não corrigida aqui): mesmo caso do create.
    with pytest.raises(ForbiddenError) as exc:
        delete_ponto(str(uuid.uuid4()), str(ponto.id))

    assert str(exc.value) == "Permissão negada"


def test_delete_ponto_inexistente_404(_db, gestor):
    with pytest.raises(NotFoundError) as exc:
        delete_ponto(str(gestor.user.id), str(uuid.uuid4()))

    assert str(exc.value) == "Ponto não encontrado"
    assert exc.value.status_code == 404


def test_delete_ponto_de_outra_prefeitura_403(_db, gestor, other_prefeitura):
    alheio = _cria_ponto(_db, other_prefeitura.id)

    with pytest.raises(ForbiddenError) as exc:
        delete_ponto(str(gestor.user.id), str(alheio.id))

    assert str(exc.value) == "Acesso negado"


def test_delete_ponto_qualquer_erro_vira_mensagem_de_ponto_em_uso(_db, gestor, ponto, monkeypatch):
    # CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui)
    # O `except Exception` genérico responde "está sendo usado em uma rota"
    # para qualquer falha, inclusive as que nada têm a ver com uso do ponto.
    def falha_generica():
        raise RuntimeError("conexão perdida")

    monkeypatch.setattr(pontos_service.db.session, "commit", falha_generica)

    with pytest.raises(AppError) as exc:
        delete_ponto(str(gestor.user.id), str(ponto.id))

    assert str(exc.value) == "Este ponto está sendo usado em uma rota e não pode ser excluído"
    assert exc.value.status_code == 400
