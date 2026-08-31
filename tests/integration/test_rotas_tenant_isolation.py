"""
A criação de rota não pode vincular pontos de outra prefeitura.

`add_ponto` já rejeita pontos de prefeitura diferente, mas `create_rota`
aceitava qualquer `ponto_id` existente. Como o endpoint recebe o ID cru do
cliente, um gestor podia montar uma rota apontando para os pontos de outro
município — vazando coordenadas de embarque entre tenants.

O comportamento esperado é o mesmo dos demais pontos inválidos: ignorar
silenciosamente e seguir com o restante da rota.
"""

import pytest

from app.models.base import db
from app.models.rota import Rota, RotaPonto
from tests.factories.geo_factory import PontoFactory


@pytest.fixture()
def ponto_de_outra_prefeitura(_db, other_prefeitura):
    p = PontoFactory(prefeitura_id=other_prefeitura.id)
    _db.session.add(p)
    _db.session.commit()
    return p


def test_create_rota_ignora_ponto_de_outra_prefeitura(gestor, _db, ponto_de_outra_prefeitura):
    resp = gestor.client.post(
        "/v1/rotas/",
        json={
            "nome": "Rota com ponto alheio",
            "pontos": [{"ponto_id": str(ponto_de_outra_prefeitura.id), "ordem": 1}],
        },
    )

    assert resp.status_code == 201

    rota_id = resp.get_json()["id"]
    vinculos = RotaPonto.query.filter_by(rota_id=rota_id).all()

    assert vinculos == [], (
        "create_rota vinculou um ponto de outra prefeitura à rota — "
        "o mesmo vazamento entre tenants que add_ponto já bloqueia"
    )


def test_create_rota_vincula_ponto_da_propria_prefeitura(gestor, _db, ponto):
    """Controle: a guarda nova não pode derrubar o caminho legítimo."""
    resp = gestor.client.post(
        "/v1/rotas/",
        json={
            "nome": "Rota own-tenant",
            "pontos": [{"ponto_id": str(ponto.id), "ordem": 1}],
        },
    )

    assert resp.status_code == 201

    rota_id = resp.get_json()["id"]
    vinculos = RotaPonto.query.filter_by(rota_id=rota_id).all()

    assert len(vinculos) == 1
    assert str(vinculos[0].ponto_id) == str(ponto.id)


def test_create_rota_mantem_pontos_validos_ao_descartar_alheio(
    gestor, _db, ponto, ponto_de_outra_prefeitura
):
    """O ponto alheio é descartado sem levar junto os pontos válidos."""
    resp = gestor.client.post(
        "/v1/rotas/",
        json={
            "nome": "Rota mista",
            "pontos": [
                {"ponto_id": str(ponto_de_outra_prefeitura.id), "ordem": 1},
                {"ponto_id": str(ponto.id), "ordem": 2},
            ],
        },
    )

    assert resp.status_code == 201

    rota_id = resp.get_json()["id"]
    vinculos = RotaPonto.query.filter_by(rota_id=rota_id).all()

    assert [str(v.ponto_id) for v in vinculos] == [str(ponto.id)]
    assert db.session.get(Rota, rota_id) is not None
