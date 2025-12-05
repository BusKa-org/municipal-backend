from .base import db, BaseModel
from sqlalchemy.orm import relationship

class Municipio(BaseModel):
    __tablename__ = "municipios"

    nome = db.Column(db.String(120), unique=True, nullable=False)
    uf = db.Column(db.String(2), nullable=False)

    # Relationships
    rotas = relationship("Rota", back_populates="municipio")
    usuarios = relationship("User", back_populates="municipio")
