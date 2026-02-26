from unittest.mock import MagicMock, patch

from app.tasks.notificacao_tasks import verificar_viagens_10min, verificar_viagens_24h


class MockViagem:
    def __init__(self):
        self.id = "viagem_1"
        self.rota_id = "rota_1"
        self.motorista_id = "motorista_1"
        self.aviso_24h_enviado = False
        self.aviso_10min_enviado = False


class MockRotaAluno:
    def __init__(self, aluno_id):
        self.aluno_id = aluno_id


class MockUser:
    def __init__(self, id, quer_receber):
        self.id = id
        self.receber_notificacoes = quer_receber


class MockInstituicao:
    def __init__(self, nome):
        self.nome = nome


class MockAluno:
    def __init__(self, id, nome_instituicao):
        self.id = id
        self.instituicao = MockInstituicao(nome_instituicao)


class MockConfirmados:
    def __init__(self, aluno_id):
        self.aluno_id = aluno_id


class MockColumn:
    def __ge__(self, other):
        return self

    def __le__(self, other):
        return self

    def __eq__(self, other):
        return self

    def is_(self, other):
        return self


@patch("app.tasks.notificacao_tasks.db.session")
@patch("app.tasks.notificacao_tasks.Viagem")
@patch("app.tasks.notificacao_tasks.RotaAluno")
@patch("app.tasks.notificacao_tasks.NotificacaoService._criar_notificacao_interna")
def test_verificar_viagens_24h(
    mock_criar_notificacao, mock_rota_aluno_class, mock_viagem_class, mock_db_session
):
    mock_app = MagicMock()

    mock_viagem_class.data = MockColumn()
    mock_viagem_class.status = MockColumn()
    mock_viagem_class.aviso_24h_enviado = MockColumn()

    mock_viagem_instance = MockViagem()
    mock_viagem_class.query.filter.return_value.all.return_value = [mock_viagem_instance]

    mock_rota_aluno_class.query.filter_by.return_value.all.return_value = [
        MockRotaAluno("aluno_ativo"),
        MockRotaAluno("aluno_mutado"),
    ]

    def mock_get_user(model, user_id):
        if user_id == "aluno_ativo":
            return MockUser(id="aluno_ativo", quer_receber=True)
        return MockUser(id="aluno_mutado", quer_receber=False)

    mock_db_session.get.side_effect = mock_get_user

    verificar_viagens_24h(mock_app)

    assert mock_criar_notificacao.call_count == 1
    mock_criar_notificacao.assert_called_with(
        usuario_id="aluno_ativo",
        titulo="⏰ Lembrete de Viagem",
        mensagem="A sua viagem da rota está agendada para amanhã. Não se esqueça de confirmar a sua presença no percurso!",
    )
    assert mock_viagem_instance.aviso_24h_enviado is True
    mock_db_session.commit.assert_called_once()


@patch("app.tasks.notificacao_tasks.db.session")
@patch("app.tasks.notificacao_tasks.Viagem")
@patch("app.tasks.notificacao_tasks.AlunosConfirmados")
@patch("app.tasks.notificacao_tasks.NotificacaoService._criar_notificacao_interna")
def test_verificar_viagens_10min(
    mock_criar_notificacao, mock_confirmados_class, mock_viagem_class, mock_db_session
):
    mock_app = MagicMock()

    mock_viagem_class.data = MockColumn()
    mock_viagem_class.status = MockColumn()
    mock_viagem_class.aviso_10min_enviado = MockColumn()

    mock_viagem_instance = MockViagem()
    mock_viagem_class.query.filter.return_value.all.return_value = [mock_viagem_instance]

    mock_confirmados_class.query.filter_by.return_value.all.return_value = [
        MockConfirmados("a1"),
        MockConfirmados("a2"),
        MockConfirmados("a3"),
    ]

    def mock_get_aluno(model, aluno_id):
        if aluno_id == "a1":
            return MockAluno("a1", "UEPB")
        if aluno_id == "a2":
            return MockAluno("a2", "UEPB")
        if aluno_id == "a3":
            return MockAluno("a3", "IFPB")

    mock_db_session.get.side_effect = mock_get_aluno

    verificar_viagens_10min(mock_app)

    assert mock_criar_notificacao.call_count == 1

    kwargs = mock_criar_notificacao.call_args.kwargs
    assert kwargs["usuario_id"] == "motorista_1"

    assert "UEPB" in kwargs["mensagem"]
    assert "IFPB" in kwargs["mensagem"]
    assert "UEPB, UEPB" not in kwargs["mensagem"]

    assert mock_viagem_instance.aviso_10min_enviado is True
    mock_db_session.commit.assert_called_once()
