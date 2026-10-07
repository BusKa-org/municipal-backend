"""Brazil-specific input validation. Generic validators (UUID, email,
password) moved to buska_core.validation — import from there directly."""

import re

from buska_core.exceptions import ValidationError


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
