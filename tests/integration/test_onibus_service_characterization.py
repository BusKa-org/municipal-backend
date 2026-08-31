"""Characterization tests for ``app/services/onibus_service.py``.

Purpose: pin the CURRENT observable behaviour of every public function in the
module so the upcoming refactor can be proven behaviour-preserving. These are
deliberately NOT "should" tests: where the behaviour pinned here is a known
bug, the test name and comment say so. If one of these tests changes in
the SAME PR that changes the behaviour of
`onibus_service.py`, the change was not a refactor.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy.exc import DataError

from app.core.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models.onibus import Onibus
from app.models.rota import Rota
from app.services.onibus_service import (
    create_onibus,
    delete_onibus,
    get_by_id,
    list_all,
    update_onibus,
)
from tests.factories.onibus_factory import OnibusFactory
from tests.factories.viagem_factory import ViagemFactory

pytestmark = pytest.mark.integration


# ─── helpers ────────────────────────────────────────────────────────────────


def _cria_onibus(_db, prefeitura_id, placa="ABC1D23"):
    o = OnibusFactory(prefeitura_id=prefeitura_id, placa=placa, modelo="Marcopolo", capacidade=40)
    _db.session.add(o)
    _db.session.commit()
    return o


# ─── list_all ───────────────────────────────────────────────────────────────


def test_list_all_retorna_onibus_da_prefeitura_do_usuario(_db, gestor, onibus):
    resultado = list_all(str(gestor.user.id))

    assert [o.id for o in resultado] == [onibus.id]


def test_list_all_nao_vaza_onibus_de_outra_prefeitura(_db, gestor, other_prefeitura, onibus):
    alheio = _cria_onibus(_db, other_prefeitura.id, placa="XYZ9Z99")

    resultado = list_all(str(gestor.user.id))

    assert alheio.id not in [o.id for o in resultado]


def test_list_all_nao_exige_papel_aluno_lista_a_frota(_db, aluno, onibus):
    # Nenhum gate de papel: ALUNO enxerga a frota da própria prefeitura.
    resultado = list_all(str(aluno.user.id))

    assert [o.id for o in resultado] == [onibus.id]


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


def test_get_by_id_gestor_recebe_onibus_da_propria_prefeitura(_db, gestor, onibus):
    resultado = get_by_id(str(gestor.user.id), str(onibus.id))

    assert resultado.id == onibus.id


def test_get_by_id_nao_exige_papel_aluno_le_a_frota(_db, aluno, onibus):
    # Nenhum gate de papel na leitura individual.
    resultado = get_by_id(str(aluno.user.id), str(onibus.id))

    assert resultado.id == onibus.id


def test_get_by_id_usuario_inexistente_404(_db, onibus):
    with pytest.raises(NotFoundError) as exc:
        get_by_id(str(uuid.uuid4()), str(onibus.id))

    assert str(exc.value) == "Usuário não encontrado"
    assert exc.value.status_code == 404


def test_get_by_id_onibus_inexistente_404(_db, gestor):
    with pytest.raises(NotFoundError) as exc:
        get_by_id(str(gestor.user.id), str(uuid.uuid4()))

    assert str(exc.value) == "Ônibus não encontrado"
    assert exc.value.status_code == 404


def test_get_by_id_cross_tenant_403(_db, gestor, other_prefeitura):
    alheio = _cria_onibus(_db, other_prefeitura.id, placa="XYZ9Z99")

    with pytest.raises(ForbiddenError) as exc:
        get_by_id(str(gestor.user.id), str(alheio.id))

    assert str(exc.value) == "Acesso negado a este recurso"
    assert exc.value.status_code == 403


def test_get_by_id_nao_valida_formato_de_uuid_do_onibus(_db, gestor):
    # CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui)
    # Mesmo caso do `list_all`: id malformado vira DataError e 500.
    with pytest.raises(DataError):
        get_by_id(str(gestor.user.id), "nao-e-uuid")


# ─── create_onibus ──────────────────────────────────────────────────────────


def test_create_onibus_gestor_cria_e_normaliza_placa_e_modelo(_db, gestor, prefeitura):
    resultado = create_onibus(
        str(gestor.user.id),
        {"placa": " abc1d23 ", "modelo": "  Volare  ", "capacidade": 22},
    )

    assert resultado.placa == "ABC1D23"
    assert resultado.modelo == "Volare"
    assert resultado.capacidade == 22
    assert resultado.prefeitura_id == prefeitura.id
    assert Onibus.query.get(resultado.id) is not None


def test_create_onibus_aluno_403(_db, aluno):
    with pytest.raises(ForbiddenError) as exc:
        create_onibus(str(aluno.user.id), {"placa": "ABC1D23", "capacidade": 10})

    assert str(exc.value) == "Apenas gestores podem gerenciar a frota"
    assert exc.value.status_code == 403


def test_create_onibus_motorista_403(_db, motorista):
    with pytest.raises(ForbiddenError) as exc:
        create_onibus(str(motorista.user.id), {"placa": "ABC1D23", "capacidade": 10})

    assert str(exc.value) == "Apenas gestores podem gerenciar a frota"
    assert exc.value.status_code == 403


def test_create_onibus_usuario_inexistente_403(_db):
    # CARACTERIZAÇÃO DE DIVERGÊNCIA (não corrigida aqui)
    # Usuário que não existe cai no mesmo ramo do papel errado e recebe 403,
    # enquanto `list_all` e `get_by_id` devolvem 404 no mesmo cenário.
    with pytest.raises(ForbiddenError) as exc:
        create_onibus(str(uuid.uuid4()), {"placa": "ABC1D23", "capacidade": 10})

    assert str(exc.value) == "Apenas gestores podem gerenciar a frota"
    assert exc.value.status_code == 403


def test_create_onibus_sem_placa_400(_db, gestor):
    with pytest.raises(ValidationError) as exc:
        create_onibus(str(gestor.user.id), {"capacidade": 10})

    assert str(exc.value) == "Placa e Capacidade são obrigatórios"
    assert exc.value.status_code == 400


def test_create_onibus_placa_so_com_espacos_400(_db, gestor):
    with pytest.raises(ValidationError) as exc:
        create_onibus(str(gestor.user.id), {"placa": "   ", "capacidade": 10})

    assert str(exc.value) == "Placa e Capacidade são obrigatórios"


def test_create_onibus_sem_capacidade_400(_db, gestor):
    with pytest.raises(ValidationError) as exc:
        create_onibus(str(gestor.user.id), {"placa": "ABC1D23"})

    assert str(exc.value) == "Placa e Capacidade são obrigatórios"


def test_create_onibus_capacidade_zero_cai_na_mensagem_de_obrigatorio(_db, gestor):
    # CARACTERIZAÇÃO DE DIVERGÊNCIA (não corrigida aqui)
    # O teste é `not capacidade`, então 0 é tratado como campo ausente e a
    # mensagem fala em obrigatoriedade em vez de valor inválido.
    with pytest.raises(ValidationError) as exc:
        create_onibus(str(gestor.user.id), {"placa": "ABC1D23", "capacidade": 0})

    assert str(exc.value) == "Placa e Capacidade são obrigatórios"


def test_create_onibus_aceita_capacidade_negativa(_db, gestor):
    # CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui)
    # `create` não valida o valor da capacidade, só a presença. Capacidade
    # negativa é aceita e persistida. `update_onibus` valida o mesmo campo.
    resultado = create_onibus(str(gestor.user.id), {"placa": "ABC1D23", "capacidade": -5})

    assert resultado.capacidade == -5


def test_create_onibus_placa_nula_quebra_com_attribute_error(_db, gestor):
    # CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui)
    # `data.get("placa", "")` devolve None quando a chave existe com valor
    # nulo, e `None.upper()` estoura AttributeError, virando 500 genérico.
    with pytest.raises(AttributeError):
        create_onibus(str(gestor.user.id), {"placa": None, "capacidade": 10})


def test_create_onibus_placa_duplicada_409(_db, gestor, prefeitura):
    _cria_onibus(_db, prefeitura.id, placa="ABC1D23")

    with pytest.raises(ConflictError) as exc:
        create_onibus(str(gestor.user.id), {"placa": "abc1d23", "capacidade": 10})

    assert str(exc.value) == "Já existe um ônibus com a placa ABC1D23"
    assert exc.value.status_code == 409


def test_create_onibus_placa_duplicada_de_outra_prefeitura_409(_db, gestor, other_prefeitura):
    # CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui)
    # A checagem de placa é global, sem filtro de prefeitura. Um gestor
    # descobre que existe ônibus com aquela placa em outra prefeitura e fica
    # impedido de cadastrar a mesma placa na sua.
    _cria_onibus(_db, other_prefeitura.id, placa="ABC1D23")

    with pytest.raises(ConflictError) as exc:
        create_onibus(str(gestor.user.id), {"placa": "ABC1D23", "capacidade": 10})

    assert str(exc.value) == "Já existe um ônibus com a placa ABC1D23"


def test_create_onibus_sem_modelo_grava_string_vazia(_db, gestor):
    resultado = create_onibus(str(gestor.user.id), {"placa": "ABC1D23", "capacidade": 10})

    assert resultado.modelo == ""


def test_create_onibus_capacidade_nao_numerica_vira_500_com_detalhe_do_banco(_db, gestor):
    # CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui)
    # Capacidade textual só falha no commit. O `except Exception` embrulha o
    # erro do banco em AppError 500 e coloca a mensagem crua do driver na
    # resposta da API.
    with pytest.raises(AppError) as exc:
        create_onibus(str(gestor.user.id), {"placa": "ABC1D23", "capacidade": "muitos"})

    assert exc.value.status_code == 500
    assert str(exc.value).startswith("Erro ao salvar ônibus:")


# ─── update_onibus ──────────────────────────────────────────────────────────


def test_update_onibus_gestor_atualiza_e_normaliza_campos(_db, gestor, onibus):
    resultado = update_onibus(
        str(gestor.user.id),
        str(onibus.id),
        {"placa": " zzz9z99 ", "modelo": "  Volare  ", "capacidade": 33},
    )

    assert resultado.placa == "ZZZ9Z99"
    assert resultado.modelo == "Volare"
    assert resultado.capacidade == 33


def test_update_onibus_aluno_403(_db, aluno, onibus):
    with pytest.raises(ForbiddenError) as exc:
        update_onibus(str(aluno.user.id), str(onibus.id), {"modelo": "Novo"})

    assert str(exc.value) == "Apenas gestores podem gerenciar a frota"
    assert exc.value.status_code == 403


def test_update_onibus_usuario_inexistente_403(_db, onibus):
    # CARACTERIZAÇÃO DE DIVERGÊNCIA (não corrigida aqui)
    # Mesmo caso do `create_onibus`: usuário inexistente recebe 403.
    with pytest.raises(ForbiddenError) as exc:
        update_onibus(str(uuid.uuid4()), str(onibus.id), {"modelo": "Novo"})

    assert str(exc.value) == "Apenas gestores podem gerenciar a frota"


def test_update_onibus_inexistente_404(_db, gestor):
    with pytest.raises(NotFoundError) as exc:
        update_onibus(str(gestor.user.id), str(uuid.uuid4()), {"modelo": "Novo"})

    assert str(exc.value) == "Ônibus não encontrado"
    assert exc.value.status_code == 404


def test_update_onibus_cross_tenant_403_com_outra_mensagem(_db, gestor, other_prefeitura):
    # CARACTERIZAÇÃO DE DIVERGÊNCIA (não corrigida aqui)
    # A mesma violação de tenant devolve "Acesso negado a este recurso" no
    # `get_by_id` e "Proibido alterar dados de outra prefeitura" aqui.
    alheio = _cria_onibus(_db, other_prefeitura.id, placa="XYZ9Z99")

    with pytest.raises(ForbiddenError) as exc:
        update_onibus(str(gestor.user.id), str(alheio.id), {"modelo": "Novo"})

    assert str(exc.value) == "Proibido alterar dados de outra prefeitura"
    assert exc.value.status_code == 403


def test_update_onibus_placa_duplicada_409_com_campo(_db, gestor, prefeitura, onibus):
    _cria_onibus(_db, prefeitura.id, placa="ABC1D23")

    with pytest.raises(ConflictError) as exc:
        update_onibus(str(gestor.user.id), str(onibus.id), {"placa": "abc1d23"})

    assert str(exc.value) == "Já existe um ônibus com a placa ABC1D23"
    assert exc.value.status_code == 409
    assert exc.value.field == "placa"


def test_update_onibus_manter_a_propria_placa_nao_da_conflito(_db, gestor, prefeitura):
    o = _cria_onibus(_db, prefeitura.id, placa="ABC1D23")

    resultado = update_onibus(str(gestor.user.id), str(o.id), {"placa": "ABC1D23"})

    assert resultado.placa == "ABC1D23"


def test_update_onibus_placa_vazia_e_ignorada(_db, gestor, onibus):
    # O walrus testa a verdade do valor, então string vazia não limpa o campo:
    # a placa antiga permanece.
    placa_antiga = onibus.placa

    resultado = update_onibus(str(gestor.user.id), str(onibus.id), {"placa": ""})

    assert resultado.placa == placa_antiga


def test_update_onibus_modelo_vazio_e_ignorado(_db, gestor, onibus):
    modelo_antigo = onibus.modelo

    resultado = update_onibus(str(gestor.user.id), str(onibus.id), {"modelo": ""})

    assert resultado.modelo == modelo_antigo


def test_update_onibus_capacidade_ausente_e_ignorada(_db, gestor, onibus):
    capacidade_antiga = onibus.capacidade

    resultado = update_onibus(str(gestor.user.id), str(onibus.id), {"modelo": "Novo"})

    assert resultado.capacidade == capacidade_antiga


def test_update_onibus_capacidade_nula_e_ignorada(_db, gestor, onibus):
    capacidade_antiga = onibus.capacidade

    resultado = update_onibus(str(gestor.user.id), str(onibus.id), {"capacidade": None})

    assert resultado.capacidade == capacidade_antiga


def test_update_onibus_capacidade_zero_400(_db, gestor, onibus):
    with pytest.raises(ValidationError) as exc:
        update_onibus(str(gestor.user.id), str(onibus.id), {"capacidade": 0})

    assert str(exc.value) == "Capacidade deve ser um número inteiro positivo"
    assert exc.value.status_code == 400


def test_update_onibus_capacidade_textual_400(_db, gestor, onibus):
    # Aqui a capacidade textual é barrada antes do banco, ao contrário do
    # `create_onibus`, que só quebra no commit.
    with pytest.raises(ValidationError) as exc:
        update_onibus(str(gestor.user.id), str(onibus.id), {"capacidade": "muitos"})

    assert str(exc.value) == "Capacidade deve ser um número inteiro positivo"


def test_update_onibus_capacidade_invalida_nao_desfaz_placa_ja_atribuida(_db, gestor, onibus):
    # CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui)
    # A placa é atribuída ao objeto antes de a capacidade ser validada. Ao
    # levantar ValidationError não há rollback, então o objeto fica sujo na
    # sessão e qualquer commit posterior grava a placa nova.
    with pytest.raises(ValidationError):
        update_onibus(str(gestor.user.id), str(onibus.id), {"placa": "ZZZ9Z99", "capacidade": 0})

    assert onibus.placa == "ZZZ9Z99"


def test_update_onibus_modelo_longo_demais_500_vaza_o_erro_do_banco(_db, gestor, onibus):
    # CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui)
    # `modelo` é String(50) e não tem validação de tamanho no serviço. O erro
    # do Postgres estoura no commit e vira 500 com o texto do banco no corpo,
    # para uma entrada que é inválida do lado do cliente.
    with pytest.raises(AppError) as exc:
        update_onibus(str(gestor.user.id), str(onibus.id), {"modelo": "M" * 51})

    assert exc.value.status_code == 500
    assert str(exc.value).startswith("Erro ao atualizar ônibus: ")
    assert "StringDataRightTruncation" in str(exc.value)


# ─── delete_onibus ──────────────────────────────────────────────────────────


def test_delete_onibus_gestor_remove(_db, gestor, onibus):
    onibus_id = onibus.id

    assert delete_onibus(str(gestor.user.id), str(onibus_id)) is None

    assert Onibus.query.get(onibus_id) is None


def test_delete_onibus_aluno_403(_db, aluno, onibus):
    with pytest.raises(ForbiddenError) as exc:
        delete_onibus(str(aluno.user.id), str(onibus.id))

    assert str(exc.value) == "Apenas gestores podem gerenciar a frota"
    assert exc.value.status_code == 403


def test_delete_onibus_usuario_inexistente_403(_db, onibus):
    with pytest.raises(ForbiddenError) as exc:
        delete_onibus(str(uuid.uuid4()), str(onibus.id))

    assert str(exc.value) == "Apenas gestores podem gerenciar a frota"


def test_delete_onibus_inexistente_404(_db, gestor):
    with pytest.raises(NotFoundError) as exc:
        delete_onibus(str(gestor.user.id), str(uuid.uuid4()))

    assert str(exc.value) == "Ônibus não encontrado"
    assert exc.value.status_code == 404


def test_delete_onibus_cross_tenant_403(_db, gestor, other_prefeitura):
    alheio = _cria_onibus(_db, other_prefeitura.id, placa="XYZ9Z99")

    with pytest.raises(ForbiddenError) as exc:
        delete_onibus(str(gestor.user.id), str(alheio.id))

    assert str(exc.value) == "Proibido alterar dados de outra prefeitura"
    assert exc.value.status_code == 403


def test_delete_onibus_vinculado_a_rota_apaga_e_zera_o_veiculo_padrao(_db, gestor, onibus, rota):
    # CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui)
    # A FK de `veiculo_padrao_id` é ON DELETE SET NULL. Remover o ônibus é
    # aceito e a rota fica sem veículo padrão, em silêncio.
    delete_onibus(str(gestor.user.id), str(onibus.id))

    _db.session.expire_all()
    assert Rota.query.get(rota.id).veiculo_padrao_id is None


def test_delete_onibus_vinculado_a_viagem_400(_db, gestor, onibus):
    # A FK de `veiculo_id` na viagem é ON DELETE RESTRICT. O IntegrityError é
    # traduzido para uma mensagem de negócio com status 400.
    viagem = ViagemFactory(veiculo_id=onibus.id, data=date(2026, 8, 14))
    _db.session.add(viagem)
    _db.session.commit()

    with pytest.raises(AppError) as exc:
        delete_onibus(str(gestor.user.id), str(onibus.id))

    assert str(exc.value) == (
        "Não é possível remover este veículo pois ele possui viagens vinculadas"
    )
    assert exc.value.status_code == 400
