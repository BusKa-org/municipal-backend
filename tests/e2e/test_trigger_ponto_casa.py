"""Trigger `trg_remover_ponto_casa` (issue #76).

Precisa de Postgres real com as migrações aplicadas (`make db-create`); o
trigger é PL/pgSQL e não existe no SQLite usado pelo resto da suíte.

Cada teste roda numa transação que é sempre revertida — não suja o banco.
"""

import os
import uuid

import pytest
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def engine():
    from app.core.config import Settings

    os.environ.setdefault("DEBUG", "true")
    uri = Settings().SQLALCHEMY_DATABASE_URI
    eng = create_engine(uri)
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:  # pragma: no cover - ambiente sem banco
        pytest.skip(f"Postgres indisponível: {e}")
    return eng


@pytest.fixture()
def conn(engine):
    with engine.connect() as c:
        trans = c.begin()
        yield c
        trans.rollback()


def _prefeitura(conn):
    return conn.execute(
        text(
            "INSERT INTO prefeitura (nome, estado, codigo_ibge) "
            "VALUES ('Teste', 'PB', :ibge) RETURNING id"
        ),
        {"ibge": str(uuid.uuid4().int)[:7]},
    ).scalar_one()


def _ponto(conn, prefeitura_id):
    return conn.execute(
        text(
            "INSERT INTO ponto (prefeitura_id, latitude, longitude) "
            "VALUES (:p, -7.1, -34.8) RETURNING id"
        ),
        {"p": prefeitura_id},
    ).scalar_one()


def _aluno(conn, prefeitura_id, ponto_casa_id):
    usuario_id = conn.execute(
        text(
            "INSERT INTO usuario (prefeitura_id, nome, email, senha_hash, cpf, role, "
            "receber_notificacoes, status) "
            "VALUES (:p, 'Aluno', :email, 'x', :cpf, 'ALUNO', true, 'ACTIVE') RETURNING id"
        ),
        {
            "p": prefeitura_id,
            "email": f"{uuid.uuid4()}@teste.com",
            "cpf": str(uuid.uuid4().int)[:11],
        },
    ).scalar_one()
    conn.execute(
        text("INSERT INTO aluno (usuario_id, ponto_casa_id) VALUES (:u, :pc)"),
        {"u": usuario_id, "pc": ponto_casa_id},
    )
    return usuario_id


def _viagem(conn):
    return conn.execute(
        text(
            "INSERT INTO viagem (data, aviso_24h_enviado, aviso_10min_enviado) "
            "VALUES (CURRENT_DATE, false, false) RETURNING id"
        )
    ).scalar_one()


def _endereco(conn, ponto_id):
    return conn.execute(
        text(
            "INSERT INTO endereco (logradouro, numero, bairro, cidade, cep, ponto_id) "
            "VALUES ('Rua A', '1', 'Centro', 'JP', '58000-000', :pt) RETURNING id"
        ),
        {"pt": ponto_id},
    ).scalar_one()


def _endereco_existe(conn, endereco_id):
    return (
        conn.execute(
            text("SELECT count(*) FROM endereco WHERE id = :e"), {"e": endereco_id}
        ).scalar_one()
        > 0
    )


def _delete_aluno(conn, usuario_id):
    conn.execute(text("DELETE FROM usuario WHERE id = :u"), {"u": usuario_id})


def _ponto_existe(conn, ponto_id):
    return (
        conn.execute(text("SELECT count(*) FROM ponto WHERE id = :p"), {"p": ponto_id}).scalar_one()
        > 0
    )


def test_apaga_ponto_casa_junto_com_o_aluno(conn):
    pref = _prefeitura(conn)
    ponto = _ponto(conn, pref)
    aluno = _aluno(conn, pref, ponto)

    _delete_aluno(conn, aluno)

    assert not _ponto_existe(conn, ponto)


def test_aluno_sem_ponto_casa_e_apagado_normalmente(conn):
    pref = _prefeitura(conn)
    aluno = _aluno(conn, pref, None)

    _delete_aluno(conn, aluno)

    assert (
        conn.execute(
            text("SELECT count(*) FROM aluno WHERE usuario_id = :u"), {"u": aluno}
        ).scalar_one()
        == 0
    )


def test_preserva_ponto_usado_por_rota(conn):
    pref = _prefeitura(conn)
    ponto = _ponto(conn, pref)
    aluno = _aluno(conn, pref, ponto)
    rota = conn.execute(
        text("INSERT INTO rota (prefeitura_id, nome) VALUES (:p, 'R') RETURNING id"),
        {"p": pref},
    ).scalar_one()
    conn.execute(
        text("INSERT INTO rota_ponto (rota_id, ponto_id, ordem) VALUES (:r, :pt, 1)"),
        {"r": rota, "pt": ponto},
    )

    _delete_aluno(conn, aluno)

    assert _ponto_existe(conn, ponto)


def test_preserva_ponto_usado_por_viagem(conn):
    pref = _prefeitura(conn)
    ponto = _ponto(conn, pref)
    aluno = _aluno(conn, pref, ponto)
    viagem = _viagem(conn)
    conn.execute(
        text("INSERT INTO viagem_ponto (viagem_id, ponto_id, ordem) VALUES (:v, :pt, 1)"),
        {"v": viagem, "pt": ponto},
    )

    _delete_aluno(conn, aluno)

    assert _ponto_existe(conn, ponto)


def test_preserva_ponto_de_embarque_de_outro_aluno(conn):
    pref = _prefeitura(conn)
    ponto = _ponto(conn, pref)
    aluno = _aluno(conn, pref, ponto)
    outro = _aluno(conn, pref, None)
    conn.execute(
        text(
            "INSERT INTO alunos_confirmados (viagem_id, aluno_id, ponto_embarque_id, "
            "embarcou, tentativas_auto_checkin) VALUES (:v, :a, :pt, false, 0)"
        ),
        {"v": _viagem(conn), "a": outro, "pt": ponto},
    )

    _delete_aluno(conn, aluno)

    assert _ponto_existe(conn, ponto)


def test_confirmacao_do_proprio_aluno_nao_impede_a_limpeza(conn):
    """As linhas de `alunos_confirmados` do aluno saem por CASCADE; não contam."""
    pref = _prefeitura(conn)
    ponto = _ponto(conn, pref)
    aluno = _aluno(conn, pref, ponto)
    conn.execute(
        text(
            "INSERT INTO alunos_confirmados (viagem_id, aluno_id, ponto_embarque_id, "
            "embarcou, tentativas_auto_checkin) VALUES (:v, :a, :pt, false, 0)"
        ),
        {"v": _viagem(conn), "a": aluno, "pt": ponto},
    )

    _delete_aluno(conn, aluno)

    assert not _ponto_existe(conn, ponto)


def test_preserva_ponto_compartilhado_com_outro_aluno(conn):
    pref = _prefeitura(conn)
    ponto = _ponto(conn, pref)
    aluno = _aluno(conn, pref, ponto)
    _aluno(conn, pref, ponto)

    _delete_aluno(conn, aluno)

    assert _ponto_existe(conn, ponto)


def test_preserva_ponto_de_instituicao(conn):
    """`instituicao.ponto_id` é ON DELETE CASCADE: apagar o ponto apagaria a escola."""
    pref = _prefeitura(conn)
    ponto = _ponto(conn, pref)
    aluno = _aluno(conn, pref, ponto)
    conn.execute(
        text(
            "INSERT INTO instituicao (nome, fonte, codigo_externo, uf, prefeitura_id, ponto_id) "
            "VALUES ('Escola', 'MANUAL', :cod, 'PB', :p, :pt)"
        ),
        {"cod": str(uuid.uuid4())[:8], "p": pref, "pt": ponto},
    )

    _delete_aluno(conn, aluno)

    assert _ponto_existe(conn, ponto)


def test_apaga_o_endereco_junto_com_o_ponto(conn):
    """O endereço pendura no ponto, não no aluno, e a FK é SET NULL: sem a
    limpeza ele sobreviveria órfão, com o endereço de quem excluiu a conta."""
    pref = _prefeitura(conn)
    ponto = _ponto(conn, pref)
    endereco = _endereco(conn, ponto)
    aluno = _aluno(conn, pref, ponto)

    _delete_aluno(conn, aluno)

    assert not _endereco_existe(conn, endereco)


def test_preserva_o_endereco_quando_o_ponto_e_preservado(conn):
    """Dois alunos na mesma casa: quem fica não pode perder o endereço."""
    pref = _prefeitura(conn)
    ponto = _ponto(conn, pref)
    endereco = _endereco(conn, ponto)
    aluno = _aluno(conn, pref, ponto)
    _aluno(conn, pref, ponto)

    _delete_aluno(conn, aluno)

    assert _ponto_existe(conn, ponto)
    assert _endereco_existe(conn, endereco)
