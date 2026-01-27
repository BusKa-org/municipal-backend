import logging

from werkzeug.security import generate_password_hash, check_password_hash
from ..models.user import User, Motorista, Aluno, Gestor
from ..models.base import db
from ..models.enum import UserRole
from ..core.exceptions import (
    AppError, NotFoundError, ValidationError, ForbiddenError, 
    UnauthorizedError, ConflictError
)

logger = logging.getLogger(__name__)


class UserService:

    @staticmethod
    def get_all_users() -> list[User]:
        """Returns all users."""
        return User.query.all()

    @staticmethod
    def get_user_by_id(user_id: str) -> User:
        """
        Get user by ID.
        
        Raises: NotFoundError
        """
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado")
        return user

    @staticmethod
    def create_user(data: dict) -> User:
        """
        Create a new user.
        
        Raises: ValidationError, ConflictError, AppError
        """
        email = data.get("email", "").lower().strip()
        password = data.get("password", "").strip()
        nome = data.get("nome", "").strip()
        cpf = data.get("cpf", "").strip()
        telefone = data.get("telefone", "").strip()
        
        role_str = data.get("role", "ALUNO").upper().strip()
        try:
            role_enum = UserRole(role_str)
        except ValueError:
            raise ValidationError("Perfil inválido. Use: ALUNO, MOTORISTA, GESTOR")

        if not all([email, password, nome, cpf]):
            raise ValidationError("Dados incompletos (Email, Senha, Nome, CPF)")

        if User.query.filter((User.email == email) | (User.cpf == cpf)).first():
            raise ConflictError("Usuário já existe (Email ou CPF duplicado)")

        try:
            hashed_pw = generate_password_hash(password)

            if role_enum == UserRole.GESTOR:
                new_user = Gestor(
                    nome=nome, email=email, senha_hash=hashed_pw,
                    cpf=cpf, telefone=telefone, role=role_enum
                )
            elif role_enum == UserRole.ALUNO:
                new_user = Aluno(
                    nome=nome, email=email, senha_hash=hashed_pw,
                    cpf=cpf, telefone=telefone, role=role_enum
                )
            else:
                new_user = User(
                    nome=nome, email=email, senha_hash=hashed_pw,
                    cpf=cpf, telefone=telefone, role=role_enum
                )

            db.session.add(new_user)
            db.session.commit()
            return new_user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {e}")
            raise AppError(f"Erro ao criar usuário: {str(e)}", 500)

    @staticmethod
    def update_user(user_id: str, data: dict) -> User:
        """
        Update user data.
        
        Raises: NotFoundError, ConflictError, AppError
        """
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado")

        nome = data.get("nome")
        email = data.get("email")
        password = data.get("password")
        telefone = data.get("telefone")

        if nome:
            user.nome = nome.strip()

        if email:
            email_limpo = email.lower().strip()
            existing = User.query.filter_by(email=email_limpo).first()
            if existing and existing.id != user.id:
                raise ConflictError("Email já está em uso")
            user.email = email_limpo

        if password:
            user.senha_hash = generate_password_hash(password.strip())
            
        if telefone:
            user.telefone = telefone.strip()

        try:
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user: {e}")
            raise AppError(f"Erro ao atualizar usuário: {str(e)}", 500)

    @staticmethod
    def create_motorista(gestor_id: str, data: dict) -> Motorista:
        """
        Create a new driver (gestor only).
        
        Raises: ForbiddenError, ConflictError, AppError
        """
        gestor = db.session.get(User, gestor_id)
        
        if not gestor or str(gestor.role) != 'GESTOR':
            raise ForbiddenError("Apenas gestores podem cadastrar motoristas")

        if User.query.filter((User.email == data['email']) | (User.cpf == data['cpf'])).first():
            raise ConflictError("Email ou CPF já cadastrado")
        
        if Motorista.query.filter_by(cnh=data['cnh']).first():
            raise ConflictError("CNH já cadastrada")

        try:
            novo_motorista = Motorista(
                prefeitura_id=gestor.prefeitura_id,
                nome=data['nome'],
                email=data['email'],
                senha_hash=generate_password_hash(data['password']),
                cpf=data['cpf'],
                telefone=data['telefone'],
                role=UserRole.MOTORISTA,
                cnh=data['cnh']
            )

            db.session.add(novo_motorista)
            db.session.commit()
            return novo_motorista

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating driver: {e}")
            raise AppError(f"Erro ao criar motorista: {str(e)}", 500)

    @staticmethod
    def change_password(user_id: str, data: dict) -> None:
        """
        Change user password (requires current password).
        
        Raises: ValidationError, NotFoundError, UnauthorizedError, AppError
        """
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            raise ValidationError("Senha atual e nova senha são obrigatórias")

        user = User.query.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado")

        if not check_password_hash(user.senha_hash, current_password):
            raise UnauthorizedError("A senha atual está incorreta")

        try:
            user.senha_hash = generate_password_hash(new_password)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error changing password: {e}")
            raise AppError(f"Erro ao atualizar senha: {str(e)}", 500)