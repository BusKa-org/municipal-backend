import uuid
from .base import db
from sqlalchemy.dialects.postgresql import UUID

class Prefeitura(db.Model):
    __tablename__ = 'prefeitura'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = db.Column(db.String(150), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    usuarios = db.relationship('User', backref='prefeitura', lazy=True)