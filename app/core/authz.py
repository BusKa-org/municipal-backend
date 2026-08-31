"""Authorization primitives shared across services.

Lives in ``app.core`` (not ``app.services``) so that any service can depend on
it without creating import cycles between service modules.
"""

import logging
from typing import cast

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.base import db
from app.models.enum import UserRole
from app.models.user import Gestor, User
from app.utils import validate_uuid

logger = logging.getLogger(__name__)


def get_user_or_404(user_id: str) -> User:
    """Get user by ID or raise NotFoundError."""
    validate_uuid(user_id, "User ID")
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")
    return user


def get_gestor_or_403(
    user_id: str, message: str = "Apenas gestores podem executar esta ação"
) -> Gestor:
    """Resolve ``user_id`` and assert it is a gestor, else raise ForbiddenError."""
    user = get_user_or_404(user_id)
    if user.role != UserRole.GESTOR:
        raise ForbiddenError(message)
    return cast(Gestor, user)
