"""Testes da própria fixture `query_counter`.

Infraestrutura de teste sem teste é infraestrutura em que não se pode confiar:
se o contador silenciosamente contasse zero, todo teste de N+1 escrito em cima
dele passaria sem provar nada.
"""

import pytest
from sqlalchemy import text

from app.models.prefeitura import Prefeitura


@pytest.mark.integration
def test_conta_as_queries_emitidas_no_bloco(query_counter, _db):
    with query_counter() as qc:
        _db.session.execute(text("SELECT 1"))
        _db.session.execute(text("SELECT 1"))

    assert qc.count == 2


@pytest.mark.integration
def test_nao_conta_queries_fora_do_bloco(query_counter, _db):
    with query_counter() as qc:
        _db.session.execute(text("SELECT 1"))

    _db.session.execute(text("SELECT 1"))
    _db.session.execute(text("SELECT 1"))

    # O listener precisa ter sido removido na saída do bloco. Se vazasse,
    # contaminaria todos os testes seguintes da sessão.
    assert qc.count == 1


@pytest.mark.integration
def test_listener_e_removido_mesmo_se_o_bloco_levantar(query_counter, _db):
    with pytest.raises(RuntimeError):
        with query_counter() as qc:
            _db.session.execute(text("SELECT 1"))
            raise RuntimeError("boom")

    _db.session.execute(text("SELECT 1"))
    assert qc.count == 1


@pytest.mark.integration
def test_matching_filtra_por_fragmento(query_counter, _db, prefeitura):
    with query_counter() as qc:
        Prefeitura.query.filter_by(id=prefeitura.id).first()

    assert qc.matching("prefeitura")
    assert not qc.matching("essa_tabela_nao_existe")


@pytest.mark.integration
def test_report_agrupa_por_statement_repetido(query_counter, _db):
    with query_counter() as qc:
        for _ in range(3):
            _db.session.execute(text("SELECT 1"))

    report = qc.report()
    assert "3 queries" in report
    assert "3x" in report


@pytest.mark.integration
def test_assert_at_most_falha_mostrando_o_sql(query_counter, _db):
    with query_counter() as qc:
        for _ in range(3):
            _db.session.execute(text("SELECT 1"))

    qc.assert_at_most(3)

    with pytest.raises(AssertionError, match="esperava no máximo 2 queries, saíram 3"):
        qc.assert_at_most(2)
