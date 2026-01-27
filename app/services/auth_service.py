import logging
from app import db
from app.models.user import User, Aluno, Motorista, Gestor
from app.models.enum import UserRole
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app.models.prefeitura import Prefeitura
from app.core.exceptions import (
    AppError, NotFoundError, ValidationError, UnauthorizedError, ConflictError
)

logger = logging.getLogger(__name__)


class AuthService:
            
    @staticmethod
    def login_user(data: dict) -> dict:
        """
        Authenticate user and return JWT token.
        
        Returns: dict with token and user info
        Raises: UnauthorizedError
        """
        user = User.query.filter_by(email=data.get('email')).first()

        if not user or not check_password_hash(user.senha_hash, data.get('password')):
            raise UnauthorizedError("Credenciais inválidas")
        
        access_token = create_access_token(
            identity=str(user.id), 
            additional_claims={"role": str(user.role)}
        )
        
        return {
            "message": "Login successful",
            "token": access_token,
            "user": {
                "id": str(user.id),
                "nome": user.nome,
                "email": user.email,
                "role": str(user.role)
            }
        }

    @staticmethod
    def register_user(data: dict) -> User:
        """
        Register a new user (admin/dev endpoint).
        
        Returns: User object
        Raises: ValidationError, NotFoundError, ConflictError, AppError
        """
        prefeitura_id = data.get('prefeitura_id')
        if not prefeitura_id:
            raise ValidationError("Prefeitura ID is required")
        
        if not Prefeitura.query.get(prefeitura_id):
            raise NotFoundError("Prefeitura not found")
        
        if User.query.filter((User.email == data['email']) | (User.cpf == data['cpf'])).first():
            raise ConflictError("Email or CPF already registered")

        role_str = data.get('role', 'ALUNO').upper()
        try:
            role_enum = UserRole(role_str)
        except ValueError:
            raise ValidationError("Invalid role. Use: ALUNO, MOTORISTA, GESTOR")

        if role_enum == UserRole.MOTORISTA:
            if not data.get('cnh'):
                raise ValidationError("CNH is required for Motorista")
            if Motorista.query.filter_by(cnh=data.get('cnh')).first():
                raise ConflictError("CNH already registered")

        try:
            hashed_pw = generate_password_hash(data['password'])
            
            if role_enum == UserRole.ALUNO:
                new_user = Aluno(
                    prefeitura_id=prefeitura_id,
                    nome=data['nome'],
                    email=data['email'],
                    senha_hash=hashed_pw,
                    telefone=data.get('telefone'),
                    cpf=data['cpf'],
                    role=role_enum,
                    matricula=data.get('matricula'),
                    nome_pai=data.get('nome_pai'),
                    nome_mae=data.get('nome_mae')
                )
            elif role_enum == UserRole.MOTORISTA:
                new_user = Motorista(
                    prefeitura_id=prefeitura_id,
                    nome=data['nome'],
                    email=data['email'],
                    senha_hash=hashed_pw,
                    telefone=data.get('telefone'),
                    cpf=data['cpf'],
                    role=role_enum,
                    cnh=data.get('cnh')
                )
            elif role_enum == UserRole.GESTOR:
                new_user = Gestor(
                    prefeitura_id=prefeitura_id,
                    nome=data['nome'],
                    email=data['email'],
                    senha_hash=hashed_pw,
                    telefone=data.get('telefone'),
                    cpf=data['cpf'],
                    role=role_enum,
                    matricula=data.get('matricula'),
                    salario=data.get('salario')
                )
            else:
                new_user = User(
                    prefeitura_id=prefeitura_id,
                    nome=data['nome'],
                    email=data['email'],
                    senha_hash=hashed_pw,
                    telefone=data.get('telefone'),
                    cpf=data['cpf'],
                    role=role_enum
                )

            db.session.add(new_user)
            db.session.commit()
            return new_user

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering user: {e}")
            raise AppError(f"Erro ao registrar usuário: {str(e)}", 500)