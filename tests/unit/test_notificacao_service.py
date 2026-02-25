from unittest.mock import patch

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.enum import UserRole
from app.services.notificacao_service import NotificacaoService


# Mock das entidades
class MockUser:
    def __init__(self, role):
        self.role = role


class MockRotaAluno:
    def __init__(self, aluno_id):
        self.aluno_id = aluno_id


@patch("app.services.notificacao_service.db.session")
@patch("app.services.notificacao_service.audit_logger")
def test_notificar_por_gestor_sucesso(mock_audit, mock_db_session):
    mock_db_session.get.return_value = MockUser(role=UserRole.GESTOR)

    with patch("app.services.notificacao_service.RotaAluno") as mock_rota_aluno:
        mock_rota_aluno.query.filter_by.return_value.all.return_value = [
            MockRotaAluno("aluno_1"),
            MockRotaAluno("aluno_2"),
        ]

        with patch.object(NotificacaoService, "_criar_notificacao_interna") as mock_criar:

            dados = {"titulo": "Aviso", "mensagem": "Teste de mensagem", "rota_id": "rota_123"}
            resultado = NotificacaoService.notificar_por_gestor("user_gestor_id", dados)

            assert resultado["message"] == "Notificação enviada para 2 aluno(s) com sucesso."
            assert mock_criar.call_count == 2
            mock_db_session.commit.assert_called_once()
            mock_audit.log_user_action.assert_called_once()


@patch("app.services.notificacao_service.db.session")
def test_notificar_por_gestor_falha_nao_eh_gestor(mock_db_session):

    mock_db_session.get.return_value = MockUser(role=UserRole.ALUNO)

    dados = {"titulo": "Aviso", "mensagem": "Teste", "rota_id": "123"}

    with pytest.raises(ForbiddenError) as excinfo:
        NotificacaoService.notificar_por_gestor("user_aluno_id", dados)

    assert "Apenas gestores" in str(excinfo.value)


@patch("app.services.notificacao_service.db.session")
def test_notificar_por_gestor_falha_sem_alunos(mock_db_session):
    mock_db_session.get.return_value = MockUser(role=UserRole.GESTOR)

    with patch("app.services.notificacao_service.RotaAluno") as mock_rota_aluno:
        mock_rota_aluno.query.filter_by.return_value.all.return_value = []

        dados = {"titulo": "Aviso", "mensagem": "Teste", "rota_id": "123"}

        with pytest.raises(NotFoundError) as excinfo:
            NotificacaoService.notificar_por_gestor("user_gestor_id", dados)

        assert "Nenhum aluno encontrado" in str(excinfo.value)
