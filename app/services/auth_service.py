"""Authentication service - login and password recovery."""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from app.core.exceptions import (
    ForbiddenError,
    UnauthorizedError,
    ValidationError,
)
from app.models.base import db
from app.models.enum import UserRole, UserStatus
from app.models.password_reset import PasswordResetToken
from app.models.user import Aluno, User
from app.utils import audit_logger, validate_email, validate_password
from app.utils.email_sender import send_email

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

    # Block disabled accounts
    if hasattr(user, "status") and user.status == UserStatus.DISABLED:
        audit_logger.log_auth(
            action="login_attempt",
            user_id=str(user.id),
            email=email,
            success=False,
            details={"reason": "account_disabled"},
        )
        raise ForbiddenError("Sua conta está desativada. Entre em contato com o gestor municipal.")

    # Block minors whose guardian has not yet consented
    if (
        user.role == UserRole.ALUNO
        and hasattr(user, "status")
        and user.status == UserStatus.PENDING_SIGNUP
    ):
        aluno = Aluno.query.get(str(user.id))
        if aluno and aluno.email_responsavel and not aluno.guardian_consented_at:
            audit_logger.log_auth(
                action="login_attempt",
                user_id=str(user.id),
                email=email,
                success=False,
                details={"reason": "pending_guardian_consent"},
            )
            raise ForbiddenError(
                f"Seu cadastro aguarda a confirmação do responsável legal. "
                f"Um e-mail foi enviado para {aluno.email_responsavel}."
            )

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


def request_password_reset(email_raw: str, base_url: str) -> None:
    """
    Send password recovery email with link if the user exists.
    Always returns without error (does not reveal if email exists).
    Raises only on validation or mail delivery failure.
    """
    try:
        email = validate_email(email_raw.strip())
    except ValidationError:
        raise ValidationError("Formato de email inválido")

    user = User.query.filter_by(email=email).first()
    print(user)
    print(email)
    if not user:
        logger.info("Password reset requested for unknown email: %s", email)
        return

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(hours=1)
    reset_record = PasswordResetToken(user_id=user.id, token=token, expires_at=expires_at)
    db.session.add(reset_record)
    db.session.commit()

    link = f"{base_url.rstrip('/')}/v1/auth/reset-password?token={token}"
    subject = "Recuperação de senha - BusKá"
    body_plain = (
        f"Olá, {user.nome}.\n\n"
        "Você solicitou a recuperação de senha no BusKá.\n\n"
        f"Acesse o link abaixo para redefinir sua senha (válido por 1 hora):\n{link}\n\n"
        "Se não foi você, ignore este e-mail.\n\n"
        "Equipe BusKá"
    )
    body_html = (
        f"<p>Olá, {user.nome}.</p>"
        "<p>Você solicitou a recuperação de senha no BusKá.</p>"
        f'<p><a href="{link}">Redefinir senha</a> (válido por 1 hora)</p>'
        "<p>Se não foi você, ignore este e-mail.</p>"
        "<p>Equipe BusKá</p>"
    )
    send_email(to=email, subject=subject, body_plain=body_plain, body_html=body_html)


def reset_password(token: str, new_password: str) -> None:
    """Reset user password using a valid token. Invalidates the token."""
    record = PasswordResetToken.query.filter_by(token=token).first()
    if not record:
        raise ValidationError("Link inválido ou expirado")
    if record.is_expired():
        db.session.delete(record)
        db.session.commit()
        raise ValidationError("Link expirado. Solicite uma nova recuperação de senha.")

    new_password = validate_password(new_password, "Nova senha")
    user = User.query.get(record.user_id)
    if not user:
        db.session.delete(record)
        db.session.commit()
        raise ValidationError("Link inválido")

    user.senha_hash = generate_password_hash(new_password)
    db.session.delete(record)
    db.session.commit()
    logger.info("Password reset completed for user %s", user.id)
