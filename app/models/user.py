from .base import db, BaseModel
from sqlalchemy.orm import relationship

class Role:
    ALUNO = "aluno"
    MOTORISTA = "motorista"
    GESTOR = "gestor"

class User(BaseModel):
    __tablename__ = "users"

    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    municipio_id = db.Column(db.Integer, db.ForeignKey("municipios.id"), nullable=True)

    # Relationships
    municipio = relationship("Municipio", back_populates="usuarios")
    rotas = relationship("Rota", back_populates="motorista")
    presencas = relationship("Presenca", back_populates="aluno")
    rotas_inscritas = relationship("RotaAluno", back_populates="aluno", cascade="all, delete-orphan")

    def is_aluno(self):
        return self.role == Role.ALUNO

    def is_motorista(self):
        return self.role == Role.MOTORISTA

    def is_gestor(self):
        return self.role == Role.GESTOR
