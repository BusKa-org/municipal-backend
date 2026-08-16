"""Characterization tests for ``app/services/instituicao_service.py``.

Purpose: pin the CURRENT observable behaviour of every public function in the
module so the upcoming refactor can be proven behaviour-preserving. These are
deliberately NOT "should" tests: where the behaviour pinned here is a known
bug, the test name and comment say so and point at the REFACTOR_PLAN.md id.
If one of these tests changes in the SAME PR that changes the behaviour of
`instituicao_service.py`, the change was not a refactor.

Ref: REFACTOR_PLAN.md, item T7.
"""

import uuid

import pytest

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models.enum import TipoInstituicao
from app.models.geo import Instituicao, Ponto
from app.services.instituicao_service import (
    create_instituicao,
    delete_instituicao,
    get_by_id,
    list_all,
    list_all_public,
)

pytestmark = pytest.mark.integration


# ─── helpers ────────────────────────────────────────────────────────────────


def _instituicao(
    _db,
    prefeitura_id,
    nome="Escola Municipal",
    sigla="EM",
    uf="PB",
    codigo_externo=None,
    com_ponto=True,
):
    """Instituicao válida. O serviço não consegue criar uma, ver B35."""
    ponto = None
    if com_ponto:
        ponto = Ponto(
            prefeitura_id=prefeitura_id, latitude=-7.21, longitude=-35.88, apelido=f"Inst: {nome}"
        )
        _db.session.add(ponto)
        _db.session.flush()

    inst = Instituicao(
        fonte="MANUAL",
        codigo_externo=codigo_externo or str(uuid.uuid4())[:12],
        nome=nome,
        sigla=sigla,
        uf=uf,
        tipo=TipoInstituicao.ESCOLA_PUBLICA,
        prefeitura_id=prefeitura_id,
        ponto_id=ponto.id if ponto else None,
    )
    _db.session.add(inst)
    _db.session.commit()
    return inst


_ENDERECO = {
    "latitude": -7.21,
    "longitude": -35.88,
    "logradouro": "Rua A",
    "numero": "10",
    "bairro": "Centro",
    "cidade": "Campina Grande",
    "cep": "58400000",
}


# ─── create_instituicao ─────────────────────────────────────────────────────


def test_create_instituicao_aluno_403(_db, aluno):
    with pytest.raises(ForbiddenError) as exc:
        create_instituicao(str(aluno.user.id), {"nome": "X", "endereco": _ENDERECO})

    assert str(exc.value) == "Permissão negada. Apenas gestores criam instituições."


def test_create_instituicao_motorista_403(_db, motorista):
    with pytest.raises(ForbiddenError) as exc:
        create_instituicao(str(motorista.user.id), {"nome": "X", "endereco": _ENDERECO})

    assert str(exc.value) == "Permissão negada. Apenas gestores criam instituições."


def test_create_instituicao_usuario_inexistente_403(_db):
    # Usuário ausente cai no mesmo ramo do papel errado e recebe 403, enquanto
    # `list_all` e `get_by_id` devolvem 404 no mesmo cenário.
    with pytest.raises(ForbiddenError) as exc:
        create_instituicao(str(uuid.uuid4()), {"nome": "X", "endereco": _ENDERECO})

    assert str(exc.value) == "Permissão negada. Apenas gestores criam instituições."


def test_create_instituicao_sem_endereco_400(_db, gestor):
    with pytest.raises(ValidationError) as exc:
        create_instituicao(str(gestor.user.id), {"nome": "X"})

    assert str(exc.value) == "Dados de endereço são obrigatórios"


def test_create_instituicao_o_proprio_tipo_padrao_do_servico_e_invalido(_db, gestor):
    """
    CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui). Ver B35.

    O serviço usa `data.get("tipo", "ESCOLA_PUBLICA")` e depois
    `TipoInstituicao(tipo_str)`. O construtor do Enum resolve por **valor**, e
    o valor do membro é `"Escola Pública"`, não `"ESCOLA_PUBLICA"`. O padrão
    do próprio serviço levanta `ValueError` antes de encostar no banco.

    Com o `transactional()` o `ValueError` sobe cru em vez de virar `AppError`
    500 com o texto embutido. O status para o cliente segue 500, agora pelo
    handler genérico.
    """
    with pytest.raises(ValueError, match="not a valid TipoInstituicao"):
        create_instituicao(
            str(gestor.user.id),
            {"nome": "Escola Nova", "cnpj": "12345678000199", "endereco": _ENDERECO},
        )


def test_create_instituicao_com_o_tipo_certo_ainda_viola_not_null(_db, gestor):
    """
    CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui). Ver B35.

    Passando o valor que o Enum aceita, a função avança e morre no commit. O
    `Instituicao(...)` do serviço passa só `nome`, `cnpj`, `tipo` e
    `ponto_id`, mas `fonte`, `codigo_externo`, `uf` e `prefeitura_id` são
    `nullable=False`. Não existe payload que faça esta função ter sucesso.

    A violação de NOT NULL é `IntegrityError`, então o `transactional()` a
    mapeia para `ConflictError` 409. O 409 é semanticamente errado, porque a
    causa é um defeito do servidor e não um conflito do cliente. Some quando o
    B35 for corrigido, que é a correção de verdade.
    """
    with pytest.raises(ConflictError) as exc:
        create_instituicao(
            str(gestor.user.id),
            {"nome": "Escola Nova", "tipo": "Escola Pública", "endereco": _ENDERECO},
        )

    assert exc.value.status_code == 409


def test_create_instituicao_nao_vaza_texto_do_driver(_db, gestor):
    """B38 corrigido: a resposta não carrega mais o SQL nem o nome da coluna
    que violou NOT NULL, só a mensagem fixa do `transactional()`."""
    with pytest.raises(ConflictError) as exc:
        create_instituicao(
            str(gestor.user.id),
            {"nome": "Escola Nova", "tipo": "Escola Pública", "endereco": _ENDERECO},
        )

    assert str(exc.value) == "Violação de integridade"
    assert "INSERT INTO" not in str(exc.value)


def test_create_instituicao_tipo_invalido_sobe_como_value_error(_db, gestor):
    # Tipo inválido é entrada do cliente e caberia 400. Continua virando 500,
    # agora pelo handler genérico em vez do `except Exception` do serviço.
    with pytest.raises(ValueError, match="not a valid TipoInstituicao"):
        create_instituicao(
            str(gestor.user.id),
            {"nome": "X", "tipo": "NAO_EXISTE", "endereco": _ENDERECO},
        )


def test_create_instituicao_faz_rollback_e_nao_deixa_ponto_orfao(_db, gestor):
    # O Ponto é criado e recebe flush antes do Instituicao. Como o commit
    # falha, o rollback do `except` desfaz o Ponto também.
    antes = Ponto.query.count()

    with pytest.raises(ConflictError):
        create_instituicao(
            str(gestor.user.id),
            {"nome": "Escola Nova", "tipo": "Escola Pública", "endereco": _ENDERECO},
        )

    assert Ponto.query.count() == antes


# ─── list_all ───────────────────────────────────────────────────────────────


def test_list_all_retorna_instituicoes_da_prefeitura(_db, gestor, prefeitura):
    inst = _instituicao(_db, prefeitura.id)

    assert [i.id for i in list_all(str(gestor.user.id))] == [inst.id]


def test_list_all_nao_vaza_instituicao_de_outra_prefeitura(
    _db, gestor, prefeitura, other_prefeitura
):
    minha = _instituicao(_db, prefeitura.id, nome="Minha")
    _instituicao(_db, other_prefeitura.id, nome="Alheia")

    assert [i.id for i in list_all(str(gestor.user.id))] == [minha.id]


def test_list_all_usuario_inexistente_404(_db):
    with pytest.raises(NotFoundError) as exc:
        list_all(str(uuid.uuid4()))

    assert str(exc.value) == "Usuário não encontrado"


def test_list_all_nao_exige_papel_de_gestor(_db, aluno, prefeitura):
    # O parâmetro se chama `gestor_id`, mas não há gate de papel: qualquer
    # usuário autenticado lista as instituições da própria prefeitura.
    inst = _instituicao(_db, prefeitura.id)

    assert [i.id for i in list_all(str(aluno.user.id))] == [inst.id]


def test_list_all_sem_instituicoes_devolve_lista_vazia(_db, gestor):
    assert list_all(str(gestor.user.id)) == []


# ─── list_all_public ────────────────────────────────────────────────────────


def test_list_all_public_sem_filtro_lista_todas_as_prefeituras(_db, prefeitura, other_prefeitura):
    # Endpoint público de cadastro: não recebe usuário e por isso não isola
    # por prefeitura, de propósito.
    a = _instituicao(_db, prefeitura.id, nome="Alfa")
    b = _instituicao(_db, other_prefeitura.id, nome="Beta")

    resultado = list_all_public({})

    assert {i.id for i in resultado} == {a.id, b.id}


def test_list_all_public_ordena_por_nome(_db, prefeitura):
    _instituicao(_db, prefeitura.id, nome="Zulu")
    _instituicao(_db, prefeitura.id, nome="Alfa")

    assert [i.nome for i in list_all_public({})] == ["Alfa", "Zulu"]


def test_list_all_public_limite_padrao_e_dez(_db, prefeitura):
    for n in range(12):
        _instituicao(_db, prefeitura.id, nome=f"Escola {n:02d}")

    assert len(list_all_public({})) == 10


def test_list_all_public_respeita_o_limite_informado(_db, prefeitura):
    for n in range(5):
        _instituicao(_db, prefeitura.id, nome=f"Escola {n}")

    assert len(list_all_public({"limit": 2})) == 2


def test_list_all_public_busca_por_nome_e_case_insensitive(_db, prefeitura):
    alvo = _instituicao(_db, prefeitura.id, nome="Colégio Dom Pedro")
    _instituicao(_db, prefeitura.id, nome="Escola Rural")

    assert [i.id for i in list_all_public({"search": "dom pedro"})] == [alvo.id]


def test_list_all_public_busca_por_sigla(_db, prefeitura):
    alvo = _instituicao(_db, prefeitura.id, nome="Universidade Federal", sigla="UFCG")
    _instituicao(_db, prefeitura.id, nome="Outra", sigla="XYZ")

    assert [i.id for i in list_all_public({"search": "UFCG"})] == [alvo.id]


def test_list_all_public_busca_por_uf(_db, prefeitura):
    alvo = _instituicao(_db, prefeitura.id, nome="Do Ceará", uf="CE")
    _instituicao(_db, prefeitura.id, nome="Da Paraíba", uf="PB")

    assert [i.id for i in list_all_public({"search": "CE"})] == [alvo.id]


def test_list_all_public_busca_pelo_nome_da_prefeitura(_db, prefeitura, other_prefeitura):
    alvo = _instituicao(_db, prefeitura.id, nome="Sem pista no nome")
    _instituicao(_db, other_prefeitura.id, nome="Também sem pista")

    resultado = list_all_public({"search": prefeitura.nome})

    assert [i.id for i in resultado] == [alvo.id]


def test_list_all_public_busca_sem_resultado_devolve_vazio(_db, prefeitura):
    _instituicao(_db, prefeitura.id, nome="Alfa")

    assert list_all_public({"search": "nao-existe-nada-assim"}) == []


def test_list_all_public_ignora_instituicao_sem_prefeitura_valida(_db, prefeitura):
    # O `join(Prefeitura)` é inner: instituição sem prefeitura casada some da
    # listagem pública em vez de aparecer sem o dado.
    _instituicao(_db, prefeitura.id, nome="Com prefeitura")

    assert len(list_all_public({})) == 1


# ─── get_by_id ──────────────────────────────────────────────────────────────


def test_get_by_id_devolve_instituicao_da_propria_prefeitura(_db, gestor, prefeitura):
    inst = _instituicao(_db, prefeitura.id)

    assert get_by_id(str(gestor.user.id), str(inst.id)).id == inst.id


def test_get_by_id_usuario_inexistente_404(_db, prefeitura):
    inst = _instituicao(_db, prefeitura.id)

    with pytest.raises(NotFoundError) as exc:
        get_by_id(str(uuid.uuid4()), str(inst.id))

    assert str(exc.value) == "Usuário não encontrado"


def test_get_by_id_instituicao_inexistente_404(_db, gestor):
    with pytest.raises(NotFoundError) as exc:
        get_by_id(str(gestor.user.id), str(uuid.uuid4()))

    assert str(exc.value) == "Instituição não encontrada"


def test_get_by_id_cross_tenant_403(_db, gestor, other_prefeitura):
    alheia = _instituicao(_db, other_prefeitura.id)

    with pytest.raises(ForbiddenError) as exc:
        get_by_id(str(gestor.user.id), str(alheia.id))

    assert str(exc.value) == "Acesso negado"


def test_get_by_id_nao_exige_papel_de_gestor(_db, aluno, prefeitura):
    inst = _instituicao(_db, prefeitura.id)

    assert get_by_id(str(aluno.user.id), str(inst.id)).id == inst.id


def test_list_all_e_get_by_id_usam_fontes_de_tenant_diferentes(
    _db, gestor, prefeitura, other_prefeitura
):
    """
    CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui).

    `list_all` filtra por `Instituicao.prefeitura_id`. `get_by_id` e
    `delete_instituicao` checam `inst.ponto.prefeitura_id`. São duas fontes de
    verdade para o mesmo tenant, e nada garante que concordem. Com uma
    instituição registrada na prefeitura do gestor mas apontando para um ponto
    da outra, ela aparece na listagem e dá 403 na leitura individual. Ver B36.
    """
    inst = _instituicao(_db, prefeitura.id, com_ponto=False)
    ponto_alheio = Ponto(
        prefeitura_id=other_prefeitura.id, latitude=-7.0, longitude=-35.0, apelido="Alheio"
    )
    _db.session.add(ponto_alheio)
    _db.session.flush()
    inst.ponto_id = ponto_alheio.id
    _db.session.commit()

    assert [i.id for i in list_all(str(gestor.user.id))] == [inst.id]

    with pytest.raises(ForbiddenError):
        get_by_id(str(gestor.user.id), str(inst.id))


def test_get_by_id_instituicao_sem_ponto_estoura_attribute_error(_db, gestor, prefeitura):
    """
    CARACTERIZAÇÃO DE FALHA CONHECIDA (não corrigida aqui).

    `ponto_id` é `nullable=True`, mas o guarda faz `inst.ponto.prefeitura_id`
    sem checar. Instituição sem ponto vira `AttributeError` e 500 genérico,
    onde 404 ou 403 caberiam. Ver B37.
    """
    inst = _instituicao(_db, prefeitura.id, com_ponto=False)

    with pytest.raises(AttributeError):
        get_by_id(str(gestor.user.id), str(inst.id))


# ─── delete_instituicao ─────────────────────────────────────────────────────


def test_delete_instituicao_remove_instituicao_e_ponto(_db, gestor, prefeitura):
    inst = _instituicao(_db, prefeitura.id)
    ponto_id = inst.ponto_id

    delete_instituicao(str(gestor.user.id), str(inst.id))

    assert _db.session.get(Instituicao, inst.id) is None
    assert _db.session.get(Ponto, ponto_id) is None


def test_delete_instituicao_apaga_o_ponto_para_remover_a_instituicao(_db, gestor, prefeitura):
    # O serviço faz `db.session.delete(inst.ponto)`, não `delete(inst)`. Quem
    # remove a instituição é o ON DELETE CASCADE da FK `ponto_id`.
    inst = _instituicao(_db, prefeitura.id)

    delete_instituicao(str(gestor.user.id), str(inst.id))
    _db.session.expire_all()

    assert Instituicao.query.count() == 0


def test_delete_instituicao_aluno_403(_db, aluno, prefeitura):
    inst = _instituicao(_db, prefeitura.id)

    with pytest.raises(ForbiddenError) as exc:
        delete_instituicao(str(aluno.user.id), str(inst.id))

    assert str(exc.value) == "Apenas gestores podem remover instituições"


def test_delete_instituicao_usuario_inexistente_403(_db, prefeitura):
    inst = _instituicao(_db, prefeitura.id)

    with pytest.raises(ForbiddenError) as exc:
        delete_instituicao(str(uuid.uuid4()), str(inst.id))

    assert str(exc.value) == "Apenas gestores podem remover instituições"


def test_delete_instituicao_inexistente_404(_db, gestor):
    with pytest.raises(NotFoundError) as exc:
        delete_instituicao(str(gestor.user.id), str(uuid.uuid4()))

    assert str(exc.value) == "Instituição não encontrada"


def test_delete_instituicao_cross_tenant_403(_db, gestor, other_prefeitura):
    alheia = _instituicao(_db, other_prefeitura.id)

    with pytest.raises(ForbiddenError) as exc:
        delete_instituicao(str(gestor.user.id), str(alheia.id))

    assert str(exc.value) == "Acesso negado"
    assert _db.session.get(Instituicao, alheia.id) is not None


def test_delete_instituicao_erro_no_commit_nao_vaza_texto_do_driver(
    _db, gestor, prefeitura, monkeypatch
):
    """B39 corrigido: a falha do commit sobe crua e o handler genérico
    responde 500 "Erro interno do servidor", sem o texto do driver."""
    from app.services import instituicao_service

    inst = _instituicao(_db, prefeitura.id)

    def falha_generica():
        raise RuntimeError("boom do driver")

    monkeypatch.setattr(instituicao_service.db.session, "commit", falha_generica)

    with pytest.raises(RuntimeError):
        delete_instituicao(str(gestor.user.id), str(inst.id))
