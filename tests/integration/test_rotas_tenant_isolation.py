"""
A criação de rota não pode vincular pontos de outra prefeitura.

`add_ponto` já rejeita pontos de prefeitura diferente, mas `create_rota`
aceitava qualquer `ponto_id` existente. Como o endpoint recebe o ID cru do
cliente, um gestor podia montar uma rota apontando para os pontos de outro
município — vazando coordenadas de embarque entre tenants.

**Decisão revista em 2026-08-16.** Este arquivo nasceu escolhendo
ignorar silenciosamente e seguir com o restante da rota. Depois que uma
correção fez o `add_ponto` levantar erro, as duas escritas de ponto do
módulo passaram a recusar de formas diferentes: uma respondia sucesso sem o
ponto, a outra abortava. A mesma ação dava resultado diferente conforme o
endpoint.

O empate foi desfeito para o lado de falhar, pelo mesmo motivo daquela
correção: o front mostra sucesso e o ponto some na próxima carga, então o
usuário não tem como saber. Os testes abaixo foram reescritos junto.
"""

import pytest

from app.models.rota import Rota, RotaPonto
from tests.factories.geo_factory import PontoFactory


@pytest.fixture()
def ponto_de_outra_prefeitura(_db, other_prefeitura):
    p = PontoFactory(prefeitura_id=other_prefeitura.id)
    _db.session.add(p)
    _db.session.commit()
    return p


def test_create_rota_recusa_ponto_de_outra_prefeitura(gestor, _db, ponto_de_outra_prefeitura):
    resp = gestor.client.post(
        "/v1/rotas/",
        json={
            "nome": "Rota com ponto alheio",
            "pontos": [{"ponto_id": str(ponto_de_outra_prefeitura.id), "ordem": 1}],
        },
    )

    assert resp.status_code == 403
    assert Rota.query.filter_by(nome="Rota com ponto alheio").count() == 0, (
        "a rota não pode nascer quando um dos pontos é recusado: "
        "o rollback do transactional desfaz tudo"
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


def test_create_rota_mista_falha_inteira_em_vez_de_aceitar_parcial(
    gestor, _db, ponto, ponto_de_outra_prefeitura
):
    """Um ponto alheio na lista aborta a criação inteira.

    Este teste era o oposto: afirmava que os pontos válidos sobreviviam ao
    descarte do alheio. A troca é a parte visível da decisão, e é o caso a
    revisitar se ela for revertida.
    """
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

    assert resp.status_code == 403
    assert Rota.query.filter_by(nome="Rota mista").count() == 0
    assert RotaPonto.query.filter_by(ponto_id=ponto.id).count() == 0
