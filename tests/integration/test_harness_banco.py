"""Testes do próprio harness: contra qual banco a suíte roda.

Existe por causa do achado do S4. O `tests/conftest.py` mandava
`SQLALCHEMY_DATABASE_URI="sqlite://"` depois de `create_app()`, o Flask-SQLAlchemy
já tinha lido a URI dentro de `init_app()` e a engine continuava apontada para o
Postgres de desenvolvimento. O config dizia uma coisa, a conexão fazia outra, e o
`drop_all()` do fixture `_db` apagava o banco de dev a cada rodada.

Cada teste aqui afirma o alvo **real** da engine. A divergência entre
`app.config` e `db.engine.url` é o que precisa continuar visível.
"""

import pytest

from tests.conftest import TEST_DB_NAME

pytestmark = pytest.mark.integration


def test_suite_roda_em_postgres(_db):
    assert _db.engine.dialect.name == "postgresql"


def test_engine_aponta_para_o_banco_de_teste(_db):
    assert _db.engine.url.database == TEST_DB_NAME


def test_engine_nao_aponta_para_o_banco_de_desenvolvimento(_db):
    assert _db.engine.url.database != "buska_db"


def test_config_e_engine_concordam(app, _db):
    """O config precisa descrever a conexão que existe de verdade."""
    assert app.config["SQLALCHEMY_DATABASE_URI"] == _db.engine.url.render_as_string(
        hide_password=False
    )
