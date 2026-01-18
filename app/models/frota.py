import uuid
from app import db
from sqlalchemy.dialects.postgresql import UUID

class Onibus(db.Model):
    __tablename__ = "onibus"

    id  = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    placa = db.Column(db.String(10), unique=True, nullable=False)
    modelo = db.Column(db.String(50))
    capacidade = db.Column(db.Integer, nullable=False)