from .base import db, BaseModel
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum

class UserRole(str, Enum):
    ALUNO = "aluno"
    MOTORISTA = "motorista"
    GESTOR = "gestor"

class User(BaseModel):
    __tablename__ = "users"

    id  = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(
        SQLEnum(UserRole, name="user_role"),
        nullable=False
    )

    municipio_id = db.Column(db.Integer, db.ForeignKey("municipios.id"), nullable=True)

    # Relationships
    municipio = relationship("Municipio", back_populates="usuarios")
    rotas = relationship("Rota", back_populates="motorista")
    presencas = relationship("Presenca", back_populates="aluno")
    rotas_inscritas = relationship("RotaAluno", back_populates="aluno", cascade="all, delete-orphan")

    def is_aluno(self):
        return self.role == UserRole.ALUNO

    def is_motorista(self):
        return self.role == UserRole.MOTORISTA

    def is_gestor(self):
        return self.role == UserRole.GESTOR
