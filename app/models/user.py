from .base import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .enum import UserRole

class User(db.Model):
    __tablename__ = 'usuario'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prefeitura_id = db.Column(UUID(as_uuid=True), db.ForeignKey('prefeitura.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    telefone = db.Column(db.String(20))
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    
    role = db.Column(db.Enum(UserRole, name='user_role'), default=UserRole.ALUNO)
    
    notificacoes = db.relationship('Notificacao', backref='usuario', lazy=True, cascade="all, delete-orphan")

    __mapper_args__ = {
        'polymorphic_identity': UserRole.USER,
        'polymorphic_on': role
    }

    def is_gestor(self):
        return self.role == UserRole.GESTOR

class Motorista(User):
    __tablename__ = 'motorista'

    usuario_id = db.Column(UUID(as_uuid=True), db.ForeignKey('usuario.id'), primary_key=True)
    cnh = db.Column(db.String(20), unique=True, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': UserRole.MOTORISTA,
    }

class Gestor(User):
    __tablename__ = 'gestor'

    usuario_id = db.Column(UUID(as_uuid=True), db.ForeignKey('usuario.id'), primary_key=True)
    matricula = db.Column(db.String(50))
    salario = db.Column(db.Numeric(10, 2))

    __mapper_args__ = {
        'polymorphic_identity': UserRole.GESTOR,
    }

class Aluno(User):
    __tablename__ = 'aluno'

    usuario_id = db.Column(UUID(as_uuid=True), db.ForeignKey('usuario.id'), primary_key=True)
    matricula = db.Column(db.String(50))
    nome_pai = db.Column(db.String(100))
    nome_mae = db.Column(db.String(100))

    __mapper_args__ = {
        'polymorphic_identity': UserRole.ALUNO,
    }