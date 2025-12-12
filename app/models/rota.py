from .base import db, BaseModel
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry

class Rota(BaseModel):
    __tablename__ = "rotas"

    nome = db.Column(db.String(120), nullable=False)
    municipio_id = db.Column(db.Integer, db.ForeignKey("municipios.id"), nullable=False)
    motorista_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)

    # Relationships
    municipio = relationship("Municipio", back_populates="rotas")
    motorista = relationship("User", back_populates="rotas")
    pontos = relationship("Ponto", back_populates="rotas", cascade="all, delete-orphan")
    viagens = relationship("Viagem", back_populates="rotas", cascade="all, delete-orphan")
    alunos_inscritos = relationship("RotaAluno", back_populates="rota", cascade="all, delete-orphan")

class Ponto(BaseModel):
    __tablename__ = "pontos"

    nome = db.Column(db.String(120), nullable=False)
    localizacao = db.Column(Geometry("POINT", srid=4326), nullable=False)
    rota_id = db.Column(db.Integer, db.ForeignKey("rotas.id"), nullable=False)

    rota = relationship("Rota", back_populates="pontos")

class RotaAluno(BaseModel):
    __tablename__ = "rotas_alunos"

    aluno_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    rota_id = db.Column(db.Integer, db.ForeignKey("rotas.id"), nullable=False)

    # Relationships
    aluno = relationship("User", back_populates="rotas_inscritas")
    rota = relationship("Rota", back_populates="alunos_inscritos")

    __table_args__ = (
        db.UniqueConstraint("aluno_id", "rota_id", name="uq_aluno_rota"),
    )
