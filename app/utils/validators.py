"""Input validation utilities for enhanced security."""

import re
import uuid

from app.core.exceptions import ValidationError
from app.utils.security import SecurityConfig


def validate_uuid(value: str, field_name: str = "ID") -> uuid.UUID:
    """
    Validate UUID format.

    Args:
        value: UUID string to validate
        field_name: Name of the field for error messages

    Returns:
        uuid.UUID object

    Raises:
        ValidationError: If the UUID format is invalid
    """
    try:
        return uuid.UUID(value, version=4)
    except (ValueError, AttributeError, TypeError):
        raise ValidationError(f"{field_name} deve ser um UUID válido")


def validate_cpf(cpf: str) -> str:
    """
    Validate Brazilian CPF (Cadastro de Pessoas Físicas).

    Args:
        cpf: CPF string to validate (can include dots and dashes)

    Returns:
        Cleaned CPF string (digits only)

    Raises:
        ValidationError: If CPF format or checksum is invalid
    """
    # Remove formatting characters
    raw_cpf = re.sub(r"[^\d]", "", cpf)

    if len(raw_cpf) != 11:
        raise ValidationError("CPF deve conter 11 dígitos")

    if raw_cpf == raw_cpf[0] * 11:
        raise ValidationError("CPF inválido")

    # Validate checksum digits
    def calculate_digit(cpf_partial: str, weight_start: int) -> int:
        """Calculate CPF checksum digit."""
        total = sum(int(cpf_partial[i]) * (weight_start - i) for i in range(len(cpf_partial)))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    first_digit = calculate_digit(raw_cpf[:9], 10)
    if first_digit != int(raw_cpf[9]):
        raise ValidationError("CPF inválido (primeiro dígito verificador)")

    second_digit = calculate_digit(raw_cpf[:10], 11)
    if second_digit != int(raw_cpf[10]):
        raise ValidationError("CPF inválido (segundo dígito verificador)")

    return raw_cpf


def validate_email(email: str) -> str:
    """
    Validate email format.

    Args:
        email: Email string to validate

    Returns:
        Lowercased email string

    Raises:
        ValidationError: If email format is invalid
    """
    email = email.strip().lower()

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        raise ValidationError("Formato de email inválido")

    disposable_domains = [
        "tempmail.com",
        "codgal.com",  # got this from: https://temp-mail.org/en/
        "quantyti.com",  # got this from: https://www.emailondeck.com/
        "virgilian.com",  # got this from: https://internxt.com/temporary-email
        "throwaway.email",
        "guerrillamail.com",
        "10minutemail.com",
    ]

    domain = email.split("@")[1]
    if domain in disposable_domains:
        raise ValidationError("Email de domínio descartável não é permitido")

    return email


def validate_password(password: str, field_name: str = "Senha") -> str:
    """
    Validate password meets minimum requirements.

    Args:
        password: Password to validate
        field_name: Field name for error messages (default: "Senha")

    Returns:
        Stripped password string

    Raises:
        ValidationError: If password doesn't meet requirements
    """
    password = password.strip()

    if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"{field_name} deve ter no mínimo {SecurityConfig.MIN_PASSWORD_LENGTH} caracteres"
        )

    return password
