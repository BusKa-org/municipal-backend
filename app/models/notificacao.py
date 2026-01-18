import uuid
from .base import db
from sqlalchemy.dialects.postgresql import UUID

class Notificacao(db.Model):
    __tablename__ = "notificacoes"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    usuario_id = db.Column(UUID(as_uuid=True), db.ForeignKey("usuario.id"), nullable=False)
    
    titulo = db.Column(db.String(120), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    enviada = db.Column(db.Boolean, default=False)
    data_envio = db.Column(db.DateTime)
    
    usuario = db.relationship("User", back_populates="notificacoes")