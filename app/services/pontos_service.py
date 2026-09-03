"""Geographic points (Ponto) service - stops management."""

import logging
from typing import Any

from app.core.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.core.transaction import transactional
from app.models.base import db
from app.models.enum import UserRole
from app.models.geo import Ponto
from app.models.user import User

logger = logging.getLogger(__name__)


def list_all(user_id: str) -> list[Ponto]:
    """List all points for user's prefeitura."""
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    return Ponto.query.filter_by(prefeitura_id=user.prefeitura_id).all()


def get_by_id(user_id: str, ponto_id: str) -> Ponto:
    """
    Get point by ID (with tenant check).

    Raises: NotFoundError, ForbiddenError
    """
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    ponto = db.session.get(Ponto, ponto_id)
    if not ponto:
        raise NotFoundError("Ponto não encontrado")

    if user.prefeitura_id != ponto.prefeitura_id:
        raise ForbiddenError("Acesso negado")

    return ponto


def create_ponto(user_id: str, data: dict[str, Any]) -> Ponto:
    """
    Create a new geographic point.

    Raises: ForbiddenError, ValidationError, AppError
    """
    user = db.session.get(User, user_id)
    if not user or user.role not in (UserRole.GESTOR, UserRole.MOTORISTA):
        raise ForbiddenError("Permissão negada")

    if not data.get("latitude") or not data.get("longitude"):
        raise ValidationError("Lat/Lon são obrigatórios")

    with transactional():
        novo_ponto = Ponto(
            prefeitura_id=user.prefeitura_id,
            apelido=data.get("apelido", "Sem Nome"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
        )

        db.session.add(novo_ponto)

    return novo_ponto


def update_ponto(user_id: str, ponto_id: str, data: dict[str, Any]) -> Ponto:
    """
    Update point data.

    Raises: ForbiddenError, NotFoundError, AppError
    """
    user = db.session.get(User, user_id)
    if not user or user.role != UserRole.GESTOR:
        raise ForbiddenError("Apenas gestores editam pontos")

    ponto = db.session.get(Ponto, ponto_id)
    if not ponto:
        raise NotFoundError("Ponto não encontrado")

    if ponto.prefeitura_id != user.prefeitura_id:
        raise ForbiddenError("Acesso negado")

    with transactional():
        # Update simple fields
        for field in ("apelido", "latitude", "longitude"):
            if field in data:
                setattr(ponto, field, data[field])

    return ponto


def delete_ponto(user_id: str, ponto_id: str) -> None:
    """
    Delete a point (if not in use).

    Raises: ForbiddenError, NotFoundError, AppError
    """
    user = db.session.get(User, user_id)
    if not user or user.role != UserRole.GESTOR:
        raise ForbiddenError("Permissão negada")

    ponto = db.session.get(Ponto, ponto_id)
    if not ponto:
        raise NotFoundError("Ponto não encontrado")

    if ponto.prefeitura_id != user.prefeitura_id:
        raise ForbiddenError("Acesso negado")

    try:
        with transactional():
            db.session.delete(ponto)
    except ConflictError as e:
        raise AppError(
            "Este ponto está sendo usado em uma rota e não pode ser excluído", 400
        ) from e
