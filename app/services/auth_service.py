"""Authentication service - login and registration."""

import logging
from typing import Any

from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from app.core.exceptions import (
    AppError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.models.base import db
from app.models.enum import UserRole
from app.models.prefeitura import Prefeitura
from app.models.user import Aluno, Gestor, Motorista, User
from app.utils import audit_logger, validate_cpf, validate_email, validate_password

logger = logging.getLogger(__name__)


def login_user(data: dict[str, Any]) -> dict[str, Any]:
    """
    Authenticate user and return JWT token.

    Args:
        data: Login credentials (email and password)

    Returns:
        dict with token and user info

    Raises:
        UnauthorizedError: If credentials are invalid
        ValidationError: If input data is invalid
    """
    email = data.get("email", "").strip()
    password = data.get("password")

    if not email or not password:
        audit_logger.log_auth(
            action="login_attempt",
            email=email or "unknown",
            success=False,
            details={"reason": "missing_credentials"},
        )
        raise UnauthorizedError("Credenciais inválidas")
    try:
        email = validate_email(email)
    except ValidationError:
        audit_logger.log_auth(
            action="login_attempt",
            email=email,
            success=False,
            details={"reason": "invalid_email_format"},
        )
        raise UnauthorizedError("Credenciais inválidas")

    user = User.query.filter_by(email=email).first()

    if not user:
        audit_logger.log_auth(
            action="login_attempt",
            email=email,
            success=False,
            details={"reason": "user_not_found"},
        )
        logger.info(f"Login attempt for non-existent user: {email}")
        raise UnauthorizedError("Credenciais inválidas")

    if not check_password_hash(user.senha_hash, password):
        audit_logger.log_auth(
            action="login_attempt",
            user_id=str(user.id),
            email=email,
            success=False,
            details={"reason": "invalid_password"},
        )
        logger.warning(f"Failed login attempt for user {user.id}: invalid password")
        raise UnauthorizedError("Credenciais inválidas")

    access_token = create_access_token(
        identity=str(user.id), additional_claims={"role": str(user.role)}
    )

    # Log successful login
    audit_logger.log_auth(
        action="login",
        user_id=str(user.id),
        email=email,
        success=True,
        details={"role": str(user.role)},
    )
    logger.info(f"User {user.id} logged in successfully")

    return {
        "message": "Login successful",
        "token": access_token,
        "user": {
            "id": str(user.id),
            "nome": user.nome,
            "email": user.email,
            "role": str(user.role),
        },
    }


def register_user(data: dict[str, Any]) -> User:
    """
    Register a new user (admin/dev endpoint).

    Args:
        data: User registration data

    Returns:
        User object

    Raises:
        ValidationError: If input data is invalid
        NotFoundError: If referenced resources don't exist
        ConflictError: If email/CPF/CNH already registered
        AppError: If database operation fails
    """
    prefeitura_id = data.get("prefeitura_id")
    if not prefeitura_id:
        raise ValidationError("Prefeitura ID is required")

    email = validate_email(data.get("email", ""))
    cpf_clean = validate_cpf(data.get("cpf", ""))

    if not Prefeitura.query.get(prefeitura_id):
        logger.warning(f"Registration attempt with invalid prefeitura_id: {prefeitura_id}")
        raise NotFoundError("Prefeitura not found")

    existing_user = User.query.filter((User.email == email) | (User.cpf == cpf_clean)).first()
    if existing_user:
        audit_logger.log_security_event(
            event_type="duplicate_registration_attempt",
            severity="medium",
            details={"email": email, "cpf": cpf_clean[:3] + "***"},
        )
        raise ConflictError("Email or CPF already registered")

    role_str = data.get("role", "ALUNO").upper()
    try:
        role_enum = UserRole(role_str)
    except ValueError:
        raise ValidationError("Invalid role. Use: ALUNO, MOTORISTA, GESTOR")

    if role_enum == UserRole.MOTORISTA:
        cnh = data.get("cnh")
        if not cnh:
            raise ValidationError("CNH is required for Motorista")

        if Motorista.query.filter_by(cnh=cnh).first():
            raise ConflictError("CNH already registered")

    # Validate password
    password = validate_password(data.get("password", ""))

    try:
        hashed_pw = generate_password_hash(password)

        if role_enum == UserRole.ALUNO:
            new_user = Aluno(
                prefeitura_id=prefeitura_id,
                nome=data["nome"],
                email=email,
                senha_hash=hashed_pw,
                telefone=data.get("telefone"),
                cpf=cpf_clean,
                role=role_enum,
                matricula=data.get("matricula"),
                nome_pai=data.get("nome_pai"),
                nome_mae=data.get("nome_mae"),
            )
        elif role_enum == UserRole.MOTORISTA:
            new_user = Motorista(
                prefeitura_id=prefeitura_id,
                nome=data["nome"],
                email=email,
                senha_hash=hashed_pw,
                telefone=data.get("telefone"),
                cpf=cpf_clean,
                role=role_enum,
                cnh=data.get("cnh"),
            )
        elif role_enum == UserRole.GESTOR:
            new_user = Gestor(
                prefeitura_id=prefeitura_id,
                nome=data["nome"],
                email=email,
                senha_hash=hashed_pw,
                telefone=data.get("telefone"),
                cpf=cpf_clean,
                role=role_enum,
                matricula=data.get("matricula"),
                salario=data.get("salario"),
            )
        else:
            new_user = User(
                prefeitura_id=prefeitura_id,
                nome=data["nome"],
                email=email,
                senha_hash=hashed_pw,
                telefone=data.get("telefone"),
                cpf=cpf_clean,
                role=role_enum,
            )

        db.session.add(new_user)
        db.session.commit()

        # Audit log successful registration
        audit_logger.log_auth(
            action="register",
            user_id=str(new_user.id),
            email=email,
            success=True,
            details={"role": role_str, "prefeitura_id": prefeitura_id},
        )
        logger.info(f"New user registered: {new_user.id} ({role_str})")

        return new_user

    except (ValidationError, ConflictError, NotFoundError):
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering user: {e}", exc_info=True)
        audit_logger.log_auth(
            action="register",
            email=email,
            success=False,
            details={"error": str(e), "role": role_str},
        )
        raise AppError(f"Erro ao registrar usuário: {str(e)}", 500)
