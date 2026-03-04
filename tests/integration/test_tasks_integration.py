import time
from datetime import datetime, timedelta

from app.models.enum import SentidoViagem, StatusViagem, UserRole
from app.models.notificacao import Notificacao
from app.models.prefeitura import Prefeitura
from app.models.rota import HorarioRota, Rota, RotaAluno
from app.models.user import Aluno, Motorista
from app.models.viagem import Viagem
from app.tasks.notificacao_tasks import verificar_viagens_24h


def test_integracao_job_24h_banco_real(app, _db):
    timestamp = str(int(time.time() * 1000))[-8:]
    cnh_unica = f"888{timestamp}"
    cpf_mot = f"999{timestamp}"
    cpf_alu = f"777{timestamp}"

    prefeitura = Prefeitura(nome=f"Pref Teste {timestamp}", estado="PB")
    _db.session.add(prefeitura)
    _db.session.flush()

    motorista = Motorista(
        nome="Motorista Isolado",
        email=f"mot_{timestamp}@teste.com",
        senha_hash="123",
        cpf=cpf_mot,
        telefone="000",
        role=UserRole.MOTORISTA,
        prefeitura_id=prefeitura.id,
        cnh=cnh_unica,
    )

    aluno = Aluno(
        nome="Aluno Isolado",
        email=f"alu_{timestamp}@teste.com",
        senha_hash="123",
        cpf=cpf_alu,
        telefone="000",
        role=UserRole.ALUNO,
        prefeitura_id=prefeitura.id,
    )

    rota = Rota(nome=f"Rota {timestamp}", prefeitura_id=prefeitura.id)

    _db.session.add_all([motorista, aluno, rota])
    _db.session.flush()

    horario = HorarioRota(rota_id=rota.id, horario_saida="12:00", sentido=SentidoViagem.IDA)
    _db.session.add(horario)
    _db.session.flush()

    inscricao = RotaAluno(rota_id=rota.id, aluno_id=aluno.usuario_id)
    _db.session.add(inscricao)

    amanha = datetime.now() + timedelta(days=1)

    viagem_teste = Viagem(
        horario_rota_id=horario.id,
        motorista_id=motorista.usuario_id,
        data=amanha.date(),
        status=StatusViagem.AGENDADA,
        aviso_24h_enviado=False,
    )
    _db.session.add(viagem_teste)

    _db.session.commit()

    notificacao_criada = None

    try:
        verificar_viagens_24h(app)

        _db.session.refresh(viagem_teste)
        assert (
            viagem_teste.aviso_24h_enviado is True
        ), "A flag anti-spam não foi atualizada no banco!"

        notificacao_criada = Notificacao.query.filter_by(
            usuario_id=aluno.usuario_id, titulo="⏰ Lembrete de Viagem"
        ).first()

        assert notificacao_criada is not None, "A notificação não foi salva no banco de dados!"
        assert "amanhã" in notificacao_criada.mensagem

    finally:
        if notificacao_criada:
            _db.session.delete(notificacao_criada)
        _db.session.delete(viagem_teste)
        _db.session.delete(inscricao)
        _db.session.delete(horario)
        _db.session.delete(rota)
        _db.session.delete(aluno)
        _db.session.delete(motorista)
        _db.session.delete(prefeitura)
        _db.session.commit()
