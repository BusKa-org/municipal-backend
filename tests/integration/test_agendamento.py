"""Testes de integração para o gerador de viagens em lote."""

from datetime import time

from app.models.enum import DiaDaSemana, SentidoViagem, StatusViagem, UserRole
from app.models.rota import DiasOperacao, HorarioRota, Rota
from app.models.user import User
from app.models.viagem import Viagem
from app.services.viagens_service import gerar_viagens_periodo


def test_gerar_viagens_periodo_cria_viagens_corretamente(app, _db, prefeitura):
    """
    Garante que a função central gera as viagens apenas para os dias da semana
    corretos e não cria viagens duplicadas se for chamada mais de uma vez.
    """
    with app.app_context():
        gestor = User(
            prefeitura_id=prefeitura.id,
            nome="Gestor Teste",
            email="gestor@teste.com",
            senha_hash="123",
            role=UserRole.GESTOR,
            cpf="12345678900",
        )
        _db.session.add(gestor)
        _db.session.flush()

        rota = Rota(prefeitura_id=prefeitura.id, nome="Rota da Faculdade")
        _db.session.add(rota)
        _db.session.flush()

        horario = HorarioRota(rota_id=rota.id, horario_saida=time(7, 0), sentido=SentidoViagem.IDA)
        _db.session.add(horario)
        _db.session.flush()

        dia_segunda = DiasOperacao(horario_rota_id=horario.id, dia=DiaDaSemana.SEG)
        dia_quarta = DiasOperacao(horario_rota_id=horario.id, dia=DiaDaSemana.QUA)

        _db.session.add_all([dia_segunda, dia_quarta])
        _db.session.commit()

        assert Viagem.query.count() == 0

        gerar_viagens_periodo(gestor_id=str(gestor.id), dias_futuros=14)

        viagens_criadas = Viagem.query.all()

        assert len(viagens_criadas) == 4

        for viagem in viagens_criadas:
            assert viagem.status == StatusViagem.AGENDADA
            assert viagem.horario_rota_id == horario.id
            assert viagem.data.weekday() in [0, 2]

        gerar_viagens_periodo(gestor_id=str(gestor.id), dias_futuros=14)

        viagens_apos_segunda_execucao = Viagem.query.count()
        assert viagens_apos_segunda_execucao == 4, "A função gerou viagens duplicadas!"
