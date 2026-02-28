import time
from datetime import datetime
from unittest.mock import patch

from app.models.base import db
from app.models.enum import SentidoViagem, StatusViagem, UserRole
from app.models.notificacao import Notificacao
from app.models.prefeitura import Prefeitura
from app.models.rota import HorarioRota, Rota
from app.models.user import Aluno, Motorista
from app.models.viagem import AlunosConfirmados, Viagem
from app.services import viagens_service


# Usamos o patch AQUI para "desligar" a internet e não mandar push de verdade pro Google durante o teste
@patch("app.services.notificacao_service.messaging.send")
def test_iniciar_viagem_notifica_apenas_confirmados(mock_messaging_send, app):
    timestamp = str(int(time.time() * 1000))[-8:]

    # ==========================================
    # 1. PREPARAÇÃO (Arrange)
    # ==========================================
    prefeitura = Prefeitura(nome=f"Pref {timestamp}", estado="PB")
    db.session.add(prefeitura)
    db.session.flush()

    motorista = Motorista(
        nome="Mot Iniciar",
        email=f"mot_{timestamp}@teste.com",
        senha_hash="123",
        cpf=f"111{timestamp}",
        telefone="000",
        role=UserRole.MOTORISTA,
        prefeitura_id=prefeitura.id,
        cnh=f"CNH{timestamp}",
    )

    # Aluno 1 (Vai na viagem)
    aluno_confirmado = Aluno(
        nome="Aluno Sim",
        email=f"sim_{timestamp}@teste.com",
        senha_hash="123",
        cpf=f"222{timestamp}",
        telefone="000",
        role=UserRole.ALUNO,
        prefeitura_id=prefeitura.id,
    )

    # Aluno 2 (Não vai na viagem)
    aluno_recusado = Aluno(
        nome="Aluno Nao",
        email=f"nao_{timestamp}@teste.com",
        senha_hash="123",
        cpf=f"333{timestamp}",
        telefone="000",
        role=UserRole.ALUNO,
        prefeitura_id=prefeitura.id,
    )

    rota = Rota(nome=f"Rota {timestamp}", prefeitura_id=prefeitura.id)

    db.session.add_all([motorista, aluno_confirmado, aluno_recusado, rota])
    db.session.flush()

    horario = HorarioRota(rota_id=rota.id, horario_saida="12:00", sentido=SentidoViagem.IDA)
    db.session.add(horario)
    db.session.flush()

    viagem = Viagem(
        horario_rota_id=horario.id,
        motorista_id=motorista.usuario_id,
        data=datetime.now().date(),
        status=StatusViagem.AGENDADA,
    )
    db.session.add(viagem)
    db.session.flush()

    presenca_sim = AlunosConfirmados(
        viagem_id=viagem.id, aluno_id=aluno_confirmado.usuario_id, confirmacao=True
    )
    presenca_nao = AlunosConfirmados(
        viagem_id=viagem.id, aluno_id=aluno_recusado.usuario_id, confirmacao=False
    )
    db.session.add_all([presenca_sim, presenca_nao])

    db.session.commit()

    notificacoes_geradas = []

    try:
        viagens_service.controlar_viagem(
            user_id=str(motorista.usuario_id), viagem_id=str(viagem.id), data={"acao": "INICIAR"}
        )

        db.session.refresh(viagem)
        assert viagem.status == StatusViagem.EM_ANDAMENTO, "O status da viagem não mudou!"

        notifs_sim = Notificacao.query.filter_by(usuario_id=aluno_confirmado.usuario_id).all()
        notifs_nao = Notificacao.query.filter_by(usuario_id=aluno_recusado.usuario_id).all()

        notificacoes_geradas.extend(notifs_sim)
        notificacoes_geradas.extend(notifs_nao)

        assert len(notifs_sim) == 1, "O aluno confirmado DEVERIA ter recebido 1 notificação!"
        assert (
            "iniciou a rota" in notifs_sim[0].mensagem.lower()
            or "iniciar a rota" in notifs_sim[0].mensagem.lower()
        )

        assert len(notifs_nao) == 0, "O aluno recusado NÃO deveria ter recebido notificação!"

    finally:
        for n in notificacoes_geradas:
            db.session.delete(n)
        db.session.delete(presenca_sim)
        db.session.delete(presenca_nao)
        db.session.delete(viagem)
        db.session.delete(horario)
        db.session.delete(rota)
        db.session.delete(aluno_recusado)
        db.session.delete(aluno_confirmado)
        db.session.delete(motorista)
        db.session.delete(prefeitura)
        db.session.commit()
