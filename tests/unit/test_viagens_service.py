from app.models.enum import StatusViagem, UserRole
from app.services.viagens_service import atualizar_localizacao


def test_atualizar_localizacao_dispara_notificacao(mocker, app):
    with app.app_context():
        mock_db = mocker.patch("app.services.viagens_service.db")
        mock_user = mocker.MagicMock(role=UserRole.MOTORISTA)
        mock_viagem = mocker.MagicMock(status=StatusViagem.EM_ANDAMENTO)

        mock_db.session.get.side_effect = [mock_user, mock_viagem]

        mock_ponto_geo = mocker.MagicMock()
        mock_ponto_geo.id = "ponto-123"
        mock_ponto_geo.apelido = "Ponto Teste"
        mock_ponto_geo.latitude = -23.5
        mock_ponto_geo.longitude = -46.6

        mock_ponto = mocker.MagicMock(aviso_aproximacao_enviado=False, ponto=mock_ponto_geo)

        # Patch nas classes em vez do .query
        mock_viagem_ponto_class = mocker.patch("app.services.viagens_service.ViagemPonto")
        mock_viagem_ponto_class.query.filter_by.return_value.order_by.return_value.all.return_value = [
            mock_ponto
        ]

        mock_conf = mocker.MagicMock()
        mock_conf.aluno_id = "aluno-123"
        mock_alunos_conf_class = mocker.patch("app.services.viagens_service.AlunosConfirmados")
        mock_alunos_conf_class.query.filter_by.return_value.all.return_value = [mock_conf]

        mocker.patch("app.services.viagens_service._calcular_distancia_metros", return_value=500)
        mock_notificar = mocker.patch(
            "app.services.viagens_service.NotificacaoService._criar_notificacao_interna"
        )

        dados_gps = {"latitude": -23.5, "longitude": -46.6}

        resultado = atualizar_localizacao(user_id="user-1", viagem_id="viagem-1", data=dados_gps)

        assert "notificados" in resultado["message"]
        mock_notificar.assert_called_once()
