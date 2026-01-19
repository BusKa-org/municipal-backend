import uuid
from .base import db
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .enum import SentidoViagem, DiaDaSemana


class Rota(db.Model):
    __tablename__ = "rota"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prefeitura_id = db.Column(UUID(as_uuid=True), db.ForeignKey('prefeitura.id'), nullable=False)    
    nome = db.Column(db.String(100), nullable=False)

    motorista_padrao_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("motorista.usuario_id")
    )

    veiculo_padrao_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("onibus.id")
    )

    motorista_padrao = relationship("Motorista")
    veiculo_padrao = relationship("Onibus")

    pontos_padrao = relationship(
        "RotaPonto",
        back_populates="rota",
        order_by="RotaPonto.ordem",
        cascade="all, delete-orphan"
    )

    grade_horarios = relationship(
        "HorarioRota",
        back_populates="rota",
        cascade="all, delete-orphan"
    )
    alunos_inscritos = relationship("RotaAluno", backref="rota", cascade="all, delete-orphan")


class RotaPonto(db.Model):
    __tablename__ = "rota_ponto"

    rota_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("rota.id"),
        primary_key=True
    )

    ponto_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ponto.id"),
        primary_key=True
    )

    ordem = db.Column(db.Integer, nullable=False)

    rota = relationship("Rota", back_populates="pontos_padrao")
    ponto = relationship("Ponto")


class HorarioRota(db.Model):
    __tablename__ = "horario_rota"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    rota_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("rota.id"),
        nullable=False
    )

    horario_saida = db.Column(db.Time, nullable=False)
    sentido = db.Column(db.Enum(SentidoViagem), nullable=False)

    rota = relationship("Rota", back_populates="grade_horarios")

    dias = relationship(
        "DiasOperacao",
        back_populates="horario",
        cascade="all, delete-orphan"
    )


class DiasOperacao(db.Model):
    __tablename__ = "dias_operacao"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    horario_rota_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("horario_rota.id"),
        nullable=False
    )

    dia = db.Column(db.Enum(DiaDaSemana), nullable=False)

    horario = relationship("HorarioRota", back_populates="dias")

class RotaAluno(db.Model):
    __tablename__ = "rota_aluno"

    rota_id = db.Column(UUID(as_uuid=True), db.ForeignKey("rota.id"), primary_key=True)
    aluno_id = db.Column(UUID(as_uuid=True), db.ForeignKey("aluno.usuario_id"), primary_key=True)
    
    data_inscricao = db.Column(db.DateTime, default=db.func.now())
