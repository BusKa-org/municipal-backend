import uuid
from .base import db
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .enum import StatusViagem

class Viagem(db.Model):
    __tablename__ = "viagem"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data = db.Column(db.Date, nullable=False)

    horario_rota_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("horario_rota.id")
    )

    motorista_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("motorista.usuario_id")
    )

    veiculo_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("onibus.id")
    )

    status = db.Column(
        db.Enum(StatusViagem),
        default=StatusViagem.AGENDADA,
        nullable=False
    )

    inicio_real = db.Column(db.DateTime)
    fim_real = db.Column(db.DateTime)
    km_real = db.Column(db.Float)

    motorista = relationship("Motorista")
    veiculo = relationship("Onibus")

    pontos_execucao = relationship(
        "ViagemPonto",
        back_populates="viagem",
        order_by="ViagemPonto.ordem",
        cascade="all, delete-orphan"
    )

    alunos_confirmados = relationship(
        "AlunosConfirmados",
        back_populates="viagem",
        cascade="all, delete-orphan"
    )


class ViagemPonto(db.Model):
    __tablename__ = "viagem_ponto"

    viagem_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("viagem.id"),
        primary_key=True
    )

    ponto_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ponto.id"),
        primary_key=True
    )

    ordem = db.Column(db.Integer, nullable=False)
    visitado = db.Column(db.Boolean, default=False)
    chegada_estimada = db.Column(db.DateTime)
    chegada_real = db.Column(db.DateTime)

    viagem = relationship("Viagem", back_populates="pontos_execucao")
    ponto = relationship("Ponto")

class AlunosConfirmados(db.Model):
    __tablename__ = "alunos_confirmados"

    viagem_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("viagem.id"),
        primary_key=True
    )

    aluno_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("aluno.usuario_id"),
        primary_key=True
    )

    confirmacao = db.Column(db.Boolean, default=True)

    ponto_embarque_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ponto.id")
    )

    ponto_destino_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ponto.id")
    )

    viagem = relationship("Viagem", back_populates="alunos_confirmados")
    aluno = relationship("Aluno")

    ponto_embarque = relationship(
        "Ponto",
        foreign_keys=[ponto_embarque_id]
    )

    ponto_destino = relationship(
        "Ponto",
        foreign_keys=[ponto_destino_id]
    )
