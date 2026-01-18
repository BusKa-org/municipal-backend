import uuid
from .base import db
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

class Ponto(db.Model):
    __tablename__ = "ponto"

    id  = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    latitude = db.Column(db.Numeric(10, 8), nullable=False)
    longitude = db.Column(db.Numeric(11, 8), nullable=False)
    apelido = db.Column(db.String(100))

    endereco = relationship(
        "Endereco", 
        uselist=False,
        back_populates="ponto"
    )
    instituicao = relationship(
        "Instituicao", 
        uselist=False, 
        back_populates="ponto"
    )

class Endereco(db.Model):
    __tablename__ = "endereco"

    id  = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    logradouro = db.Column(db.String(150))
    numero = db.Column(db.String(20))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    cep = db.Column(db.String(10))
    
    ponto_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ponto.id"),
        nullable=False
    )    
    
    ponto = relationship("Ponto", back_populates="endereco")

class Instituicao(db.Model):
    __tablename__ = "instituicao"

    id  = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(20))
    
    ponto_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ponto.id"),
        nullable=False
    )    
    ponto = relationship("Ponto", back_populates="instituicao")