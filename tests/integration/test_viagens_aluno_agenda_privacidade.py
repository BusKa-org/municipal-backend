"""
A agenda do aluno não pode expor a confirmação de outro aluno.

Os campos `status_confirmacao` e `ponto_embarque_id` são dados pessoais:
dizem se aquele aluno confirmou presença e em qual ponto ele embarca.
Quando dois alunos estão confirmados na mesma viagem, a agenda de cada um
deve refletir apenas o seu próprio registro.
"""

import pytest
from flask_jwt_extended import create_access_token

from tests.conftest import Actor, AuthenticatedClient
from tests.factories.geo_factory import PontoFactory
from tests.factories.rota_factory import RotaAlunoFactory
from tests.factories.user_factory import AlunoFactory
from tests.factories.viagem_factory import AlunosConfirmadosFactory


@pytest.fixture()
def segundo_aluno(client, app, _db, prefeitura):
    """Outro aluno da mesma prefeitura, para dividir a mesma viagem."""
    u = AlunoFactory(prefeitura_id=prefeitura.id)
    _db.session.add(u)
    _db.session.commit()

    with app.app_context():
        token = create_access_token(identity=str(u.id))

    headers = {"Authorization": f"Bearer {token}"}
    return Actor(user=u, headers=headers, client=AuthenticatedClient(client, headers))


@pytest.fixture()
def outro_ponto(_db, prefeitura):
    """Segundo ponto de embarque, distinto do fixture `ponto`."""
    p = PontoFactory(prefeitura_id=prefeitura.id)
    _db.session.add(p)
    _db.session.commit()
    return p


@pytest.fixture()
def viagem_com_dois_alunos_confirmados(
    _db,
    rota,
    rota_aluno,
    dia_operacao,
    viagem_futura_agendada_com_motorista,
    aluno,
    segundo_aluno,
    ponto,
    outro_ponto,
):
    """
    Uma viagem com dois alunos confirmados, com dados deliberadamente
    diferentes para que um registro nunca possa passar pelo outro.

    aluno         -> confirmou,     embarca em `ponto`
    segundo_aluno -> não confirmou, embarca em `outro_ponto`
    """
    viagem = viagem_futura_agendada_com_motorista

    # `rota_aluno` já inscreveu o primeiro aluno; o segundo precisa da mesma rota,
    # senão a viagem nem aparece na agenda dele.
    _db.session.add(RotaAlunoFactory(rota_id=rota.id, aluno_id=segundo_aluno.user.id))

    _db.session.add(
        AlunosConfirmadosFactory(
            viagem_id=viagem.id,
            aluno_id=aluno.user.id,
            confirmacao=True,
            ponto_embarque_id=ponto.id,
            ponto_destino_id=None,
        )
    )
    _db.session.add(
        AlunosConfirmadosFactory(
            viagem_id=viagem.id,
            aluno_id=segundo_aluno.user.id,
            confirmacao=False,
            ponto_embarque_id=outro_ponto.id,
            ponto_destino_id=None,
        )
    )
    _db.session.commit()
    return viagem


def _item_da_viagem(actor, viagem):
    """Retorna o item da agenda de `actor` correspondente a `viagem`."""
    r = actor.client.get("/v1/viagens/aluno/agenda")
    assert r.status_code == 200, r.get_data(as_text=True)

    itens = [i for i in (r.get_json() or {}).get("items", []) if i["viagem_id"] == str(viagem.id)]
    assert len(itens) == 1, f"esperava a viagem exatamente uma vez, veio {len(itens)}"
    return itens[0]


def test_agenda_mostra_apenas_a_confirmacao_do_proprio_aluno(
    viagem_com_dois_alunos_confirmados, aluno, segundo_aluno, ponto, outro_ponto
):
    """
    Cada aluno vê o seu próprio registro.

    Os dois registros têm valores opostos, então qualquer vazamento entre
    eles é detectado: se a agenda devolver o registro errado, os valores
    aparecem trocados.
    """
    viagem = viagem_com_dois_alunos_confirmados

    item_do_aluno = _item_da_viagem(aluno, viagem)
    item_do_segundo = _item_da_viagem(segundo_aluno, viagem)

    assert item_do_aluno["status_confirmacao"] is True
    assert item_do_aluno["ponto_embarque_id"] == str(ponto.id)

    assert item_do_segundo["status_confirmacao"] is False
    assert item_do_segundo["ponto_embarque_id"] == str(outro_ponto.id)


def test_agenda_nao_expoe_ponto_de_embarque_de_outro_aluno(
    viagem_com_dois_alunos_confirmados, aluno, segundo_aluno, ponto, outro_ponto
):
    """O ponto de embarque de um aluno nunca aparece na agenda do outro."""
    viagem = viagem_com_dois_alunos_confirmados

    item_do_aluno = _item_da_viagem(aluno, viagem)
    item_do_segundo = _item_da_viagem(segundo_aluno, viagem)

    assert item_do_aluno["ponto_embarque_id"] != str(outro_ponto.id)
    assert item_do_segundo["ponto_embarque_id"] != str(ponto.id)


def test_contagem_de_confirmados_continua_somando_a_viagem_inteira(
    viagem_com_dois_alunos_confirmados, aluno, segundo_aluno
):
    """
    A lotação do ônibus é um número da viagem, não do aluno.

    Filtrar os dados pessoais não pode reduzir essa contagem ao registro de
    quem pediu a agenda: os dois alunos devem ver o mesmo total.
    """
    viagem = viagem_com_dois_alunos_confirmados

    item_do_aluno = _item_da_viagem(aluno, viagem)
    item_do_segundo = _item_da_viagem(segundo_aluno, viagem)

    # apenas um dos dois confirmou presença
    assert item_do_aluno["alunos_confirmados_count"] == 1
    assert item_do_segundo["alunos_confirmados_count"] == 1
