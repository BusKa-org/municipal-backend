import uuid
from .base import db
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .enum import StatusViagem

class Viagem(db.Model):
    __tablename__ = "viagem"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data = db.Column(db.Date, nullable=False)
    horario_rota_id = db.Column(UUID(as_uuid=True), db.ForeignKey("horario_rota.id"), nullable=True)
    
    motorista_id = db.Column(UUID(as_uuid=True), db.ForeignKey("motorista.usuario_id"), nullable=True)
    veiculo_id = db.Column(UUID(as_uuid=True), db.ForeignKey("onibus.id"), nullable=True)
    
    status = db.Column(db.Enum(StatusViagem, native_enum=False), default=StatusViagem.AGENDADA)
    
    inicio_real = db.Column(db.DateTime, nullable=True)
    fim_real = db.Column(db.DateTime, nullable=True)
    km_real = db.Column(db.Numeric(10, 2), nullable=True)

    horario_rota = relationship("HorarioRota")
    motorista = relationship("Motorista")
    veiculo = relationship("Onibus")
    
    pontos_visitados = relationship(
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
    """
    Controla o progresso da viagem ponto a ponto.
    """
    __tablename__ = "viagem_ponto"

    viagem_id = db.Column(UUID(as_uuid=True), db.ForeignKey("viagem.id"), primary_key=True)
    ponto_id = db.Column(UUID(as_uuid=True), db.ForeignKey("ponto.id"), primary_key=True)
    
    ordem = db.Column(db.Integer, nullable=False)
    visitado = db.Column(db.Boolean, default=False)
    
    chegada_estimada = db.Column(db.DateTime, nullable=True)
    chegada_real = db.Column(db.DateTime, nullable=True)

    viagem = relationship("Viagem", back_populates="pontos_visitados")
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
