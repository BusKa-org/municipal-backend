"""
Custom exceptions for the BusKá API.

Usage:
    from app.core.exceptions import NotFoundError, ValidationError

    # In services:
    if not aluno:
        raise NotFoundError("Aluno não encontrado")

    # Errors are automatically caught by Flask error handlers
    # and returned as JSON responses with the correct status code.
"""

from typing import Any


class AppError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Recurso não encontrado"):
        super().__init__(message, 404)


class ValidationError(AppError):
    """Invalid input data (400)."""

    def __init__(self, message: str = "Dados inválidos", details: dict[str, Any] | None = None):
        super().__init__(message, 400)
        self.details = details or {}


class ForbiddenError(AppError):
    """Access denied (403)."""

    def __init__(self, message: str = "Acesso negado"):
        super().__init__(message, 403)


class UnauthorizedError(AppError):
    """Not authenticated (401)."""

    def __init__(self, message: str = "Não autenticado"):
        super().__init__(message, 401)


class ConflictError(AppError):
    """Resource already exists or conflict (409)."""

    def __init__(self, message: str = "Recurso já existe"):
        super().__init__(message, 409)
