import uuid
from .base import db
from sqlalchemy.dialects.postgresql import UUID

class Onibus(db.Model):
    __tablename__ = 'onibus'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    prefeitura_id = db.Column(UUID(as_uuid=True), db.ForeignKey('prefeitura.id'), nullable=False)
    
    placa = db.Column(db.String(10), unique=True, nullable=False)
    modelo = db.Column(db.String(50))
    capacidade = db.Column(db.Integer, nullable=False)
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"<Onibus {self.placa}>"