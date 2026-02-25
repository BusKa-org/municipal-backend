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
