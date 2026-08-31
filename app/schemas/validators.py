"""Input validation utilities for enhanced security."""

# app/schemas/validators.py
import re
import uuid

from marshmallow import ValidationError as MarshmallowValidationError


def validate_optional_string(value: str | None, field_name: str = "Texto") -> str | None:
    """
    Validate string.

    Args:
        value: String to validate
        field_name: Name of the field for error messages

    Returns:
        string
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise MarshmallowValidationError(f"{field_name} deve ser uma string")
    return value


def validate_uuid4(value: str, field_name: str = "ID") -> str:
    """
    Validate UUID4 format.

    Args:
        value: UUID4 string to validate
        field_name: Name of the field for error messages

    Returns:
        string UUID4

    Raises:
        ValidationError: If the UUID4 format is invalid
    """
    try:
        uuid.UUID(value, version=4)
        return value
    except (ValueError, AttributeError, TypeError):
        raise MarshmallowValidationError(f"{field_name} deve ser um UUID4 válido")


def validate_optional_cpf(value: str | None, field_name: str = "CPF") -> str | None:
    """
    Validate Brazilian CPF (Cadastro de Pessoas Físicas).

    Args:
        value: CPF string to validate (can include dots and dashes)
    """
    if not value:
        return None

    return validate_cpf(value, field_name)


def validate_cpf(value: str, field_name: str = "CPF") -> str:
    """
    Validate Brazilian CPF (Cadastro de Pessoas Físicas).

    Args:
        value: CPF string to validate (can include dots and dashes)

    Returns:
        Cleaned CPF string (digits only)

    Raises:
        ValidationError: If CPF format or checksum is invalid
    """
    if not value:
        raise MarshmallowValidationError(f"{field_name} não pode ser vazio")

    # Remove formatting characters
    raw_cpf = re.sub(r"[^\d]", "", value)

    if len(raw_cpf) != 11:
        raise MarshmallowValidationError(f"{field_name} deve conter 11 dígitos")

    if raw_cpf == raw_cpf[0] * 11:
        raise MarshmallowValidationError(f"{field_name} inválido (todos os dígitos são iguais)")

    # Validate checksum digits
    def calculate_digit(cpf_partial: str, weight_start: int) -> int:
        """Calculate CPF checksum digit."""
        total = sum(int(cpf_partial[i]) * (weight_start - i) for i in range(len(cpf_partial)))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    first_digit = calculate_digit(raw_cpf[:9], 10)
    if first_digit != int(raw_cpf[9]):
        raise MarshmallowValidationError(f"{field_name} inválido (primeiro dígito verificador)")

    second_digit = calculate_digit(raw_cpf[:10], 11)
    if second_digit != int(raw_cpf[10]):
        raise MarshmallowValidationError(f"{field_name} inválido (segundo dígito verificador)")

    return raw_cpf


def validate_optional_phone(value: str | None, field_name: str = "Telefone") -> str | None:
    """
    Validate Brazilian phone number.

    Args:
        value: Phone number string (can include formatting)

    Returns:
        Cleaned phone string (digits only)

    Raises:
        MarshmallowValidationError: If phone format is invalid
    """
    if not value:
        return None

    return validate_phone(value, field_name)


def validate_phone(value: str, field_name: str = "Telefone") -> str:
    """
    Validate Brazilian phone number.

    Args:
        value: Phone number string (can include formatting)

    Returns:
        Cleaned phone string (digits only)

    Raises:
        MarshmallowValidationError: If phone format is invalid
    """
    raw_phone = re.sub(r"[^\d]", "", value)

    if len(raw_phone) not in [10, 11]:
        raise MarshmallowValidationError(f"{field_name} deve conter 10 ou 11 dígitos (com DDD)")

    area_code = int(raw_phone[:2])
    if area_code < 11 or area_code > 99:
        raise MarshmallowValidationError(f"{field_name} DDD inválido (deve estar entre 11 e 99)")

    return raw_phone
