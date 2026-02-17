"""Testes de integração para o gerador de viagens em lote."""

import pytest
from datetime import time

from app.models.enum import DiaDaSemana, SentidoViagem, StatusViagem, UserRole
from app.models.rota import DiasOperacao, HorarioRota, Rota
from app.models.user import User
from app.models.viagem import Viagem
from app.services.viagens_service import gerar_viagens_periodo


@pytest.mark.integration
def test_gerar_viagens_periodo_cria_viagens_corretamente(gestor, prefeitura, rota, horario_rota, dia_operacao, dia_operacao_quarta):
    """
    Garante que a função central gera as viagens apenas para os dias da semana
    corretos e não cria viagens duplicadas se for chamada mais de uma vez.
    """
    assert Viagem.query.count() == 0
    gerar_viagens_periodo(gestor_id=str(gestor.user.id), dias_futuros=14)

    viagens_criadas = Viagem.query.all()

    assert len(viagens_criadas) == 4

    for viagem in viagens_criadas:
        assert viagem.status == StatusViagem.AGENDADA
        assert viagem.horario_rota_id == horario_rota.id
        assert viagem.data.weekday() in [0, 2]

    gerar_viagens_periodo(gestor_id=str(gestor.user.id), dias_futuros=14)

    viagens_apos_segunda_execucao = Viagem.query.count()
    assert viagens_apos_segunda_execucao == 4, "A função gerou viagens duplicadas!"
