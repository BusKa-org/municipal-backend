import uuid
from app import db
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

class User(db.Model):
    __tablename__ = "usuario"

    id  = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    telefone = db.Column(db.String(20))
    cpf = db.Column(db.String(14), unique=True)

    # Relationship 1:1 (uselist=False)
    aluno = relationship(
        "Aluno", 
        uselist=False, 
        back_populates="usuario", 
        cascade="all, delete-orphan"
    )
    motorista = relationship(
        "Motorista", 
        uselist=False, 
        back_populates="usuario", 
        cascade="all, delete-orphan"
    )
    gestor = relationship(
        "Gestor", 
        uselist=False, 
        back_populates="usuario", 
        cascade="all, delete-orphan"
    )

    @property
    def role(self):
        if self.gestor: 
            return "gestor"
        if self.motorista: 
            return "motorista"
        if self.aluno: 
            return "aluno"
        return "user"

class Aluno(db.Model):
    __tablename__ = "aluno"
    
    # Shared Primary Key
    usuario_id = db.Column(
        UUID(as_uuid=True), 
        db.ForeignKey("usuario.id"), 
        primary_key=True
    )
    matricula = db.Column(db.String(50))
    nome_pai = db.Column(db.String(100))
    nome_mae = db.Column(db.String(100))

    usuario = relationship("User", back_populates="aluno")

class Motorista(db.Model):
    __tablename__ = "motorista"
    
    usuario_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("usuario.id"),
        primary_key=True
    )    
    cnh = db.Column(db.String(20))

    usuario = relationship("User", back_populates="motorista")

class Gestor(db.Model):
    __tablename__ = "gestor"
    
    usuario_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("usuario.id"),
        primary_key=True
    )    
    matricula = db.Column(db.String(50))
    salario = db.Column(db.Numeric(10, 2))

    usuario = relationship("User", back_populates="gestor")