from .base import db, BaseModel
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

class Viagem(BaseModel):
    __tablename__ = "viagens"

    data = db.Column(db.Date, nullable=False)
    horario_inicio = db.Column(db.Time, nullable=False)
    horario_fim = db.Column(db.Time, nullable=True)
    tipo = db.Column(db.Enum("IDA", "VOLTA", name="tipo_viagem"), nullable=False)

    rota_id = db.Column(db.Integer, db.ForeignKey("rotas.id"), nullable=False)
    motorista_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)

    rota = relationship("Rota", back_populates="viagens")
    motorista = relationship("User")
    viagens_presenca = relationship("ViagemAluno", back_populates="viagem", cascade="all, delete-orphan")

class ViagemAluno(BaseModel):
    __tablename__ = "viagens_alunos"

    aluno_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    viagem_id = db.Column(db.Integer, db.ForeignKey("viagens.id"), nullable=False)
    confirmada = db.Column(db.Boolean, default=False)
    cancelada = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, nullable=True)

    aluno = relationship("User", back_populates="viagens_presenca")
    viagem = relationship("Viagem", back_populates="viagens_presenca")
