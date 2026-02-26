from datetime import date
from unittest.mock import patch

from app.models.enum import StatusViagem, UserRole
from app.services import viagens_service


class MockUser:
    def __init__(self, role):
        self.role = role


class MockViagem:
    def __init__(self):
        self.id = "viagem_123"
        self.status = StatusViagem.AGENDADA
        self.data = date(2026, 12, 25)


class MockConfirmados:
    def __init__(self, aluno_id):
        self.aluno_id = aluno_id


class MockPontoGeo:
    def __init__(self, lat, lon):
        self.id = "ponto_1"
        self.latitude = lat
        self.longitude = lon
        self.apelido = "Ponto Central"


class MockViagemPonto:
    def __init__(self, lat, lon):
        self.ponto = MockPontoGeo(lat, lon)
        self.aviso_aproximacao_enviado = False


@patch("app.services.viagens_service.db.session")
@patch("app.services.viagens_service.audit_logger")
@patch("app.services.viagens_service.NotificacaoService._criar_notificacao_interna")
def test_cancelar_viagem_sucesso_com_notificacao(
    mock_criar_notificacao, mock_audit, mock_db_session
):
    mock_db_session.get.side_effect = [MockUser(role=UserRole.GESTOR), MockViagem()]

    with patch("app.services.viagens_service.AlunosConfirmados") as mock_confirmados:
        mock_confirmados.query.filter_by.return_value.all.return_value = [
            MockConfirmados("aluno_1"),
            MockConfirmados("aluno_2"),
            MockConfirmados("aluno_3"),
        ]

        resultado = viagens_service.cancelar_viagem("user_gestor_id", "viagem_123")

        assert resultado["message"] == "Viagem cancelada com sucesso"
        assert resultado["alunos_notificados"] == 3
        assert mock_criar_notificacao.call_count == 3
        mock_db_session.commit.assert_called_once()
        mock_audit.log_user_action.assert_called_once()


@patch("app.services.viagens_service.db.session")
@patch("app.services.viagens_service.ViagemPonto")
@patch("app.services.viagens_service.AlunosConfirmados")
@patch("app.services.viagens_service.NotificacaoService._criar_notificacao_interna")
def test_atualizar_localizacao_dispara_notificacao(
    mock_criar_notificacao, mock_alunos_conf, mock_viagem_ponto, mock_db_session
):
    mock_motorista = MockUser(role=UserRole.MOTORISTA)
    mock_viagem = MockViagem()
    mock_viagem.status = StatusViagem.EM_ANDAMENTO

    mock_db_session.get.side_effect = [mock_motorista, mock_viagem]

    ponto_destino = MockViagemPonto(-7.2307, -35.8811)
    mock_viagem_ponto.query.filter_by.return_value.order_by.return_value.all.return_value = [
        ponto_destino
    ]

    mock_alunos_conf.query.filter_by.return_value.all.return_value = [
        MockConfirmados("aluno_1"),
        MockConfirmados("aluno_2"),
    ]

    payload_gps = {"latitude": -7.2308, "longitude": -35.8812}

    from app.services import viagens_service

    resultado = viagens_service.atualizar_localizacao("motorista_id", "viagem_123", payload_gps)

    assert "notificados" in resultado["message"]
    assert resultado["distancia_metros"] < 1000

    assert mock_criar_notificacao.call_count == 2
    assert ponto_destino.aviso_aproximacao_enviado is True
    mock_db_session.commit.assert_called_once()
