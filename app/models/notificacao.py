from .base import db, BaseModel

class Notificacao(BaseModel):
    __tablename__ = "notificacoes"

    usuario_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    titulo = db.Column(db.String(120), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    enviada = db.Column(db.Boolean, default=False)
    data_envio = db.Column(db.DateTime, nullable=True)
