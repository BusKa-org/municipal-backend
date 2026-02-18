from marshmallow import fields, validate

from app.schemas.common import BaseSchema
from app.schemas.endereco_schema import EnderecoInputSchema
from app.schemas.validators import (
    validate_cpf,
    validate_optional_cpf,
    validate_optional_phone,
    validate_optional_string,
)


class AlunoProvisionAccountRequestSchema(BaseSchema):
    """Gestor creates a minimal Aluno account (credentials + identity)."""

    nome = fields.String(required=True, validate=validate.Length(min=1))
    email = fields.Email(required=True, error_messages={"invalid": "Email inválido"})
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=1))
    cpf = fields.String(required=True, validate=validate_cpf)
    telefone = fields.String(load_default=None, allow_none=True, validate=validate_optional_phone)


class AlunoSelfSignupRequestSchema(BaseSchema):
    """Aluno self-signs up for an account."""

    nome = fields.String(required=True, validate=validate.Length(min=1))
    email = fields.Email(required=True, error_messages={"invalid": "Email inválido"})
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=1))
    cpf = fields.String(required=True, validate=validate_cpf)
    telefone = fields.String(load_default=None, allow_none=True, validate=validate_optional_phone)

    matricula = fields.String(required=True, validate=validate.Length(min=1))
    instituicao_id = fields.UUID(required=True)

    nome_pai = fields.String(load_default=None, allow_none=True, validate=validate_optional_string)
    cpf_pai = fields.String(load_default=None, allow_none=True, validate=validate_optional_cpf)
    nome_mae = fields.String(load_default=None, allow_none=True, validate=validate_optional_string)
    cpf_mae = fields.String(load_default=None, allow_none=True, validate=validate_optional_cpf)

    endereco_casa = fields.Nested(EnderecoInputSchema, required=True)


class AlunoMeUpdateRequestSchema(BaseSchema):
    """Aluno updates their profile (partial update)."""

    nome = fields.String(load_default=None, allow_none=True, validate=validate_optional_string)
    telefone = fields.String(load_default=None, allow_none=True, validate=validate_optional_phone)

    matricula = fields.String(load_default=None, allow_none=True, validate=validate_optional_string)
    nome_pai = fields.String(load_default=None, allow_none=True, validate=validate_optional_string)
    cpf_pai = fields.String(load_default=None, allow_none=True, validate=validate_optional_cpf)
    nome_mae = fields.String(load_default=None, allow_none=True, validate=validate_optional_string)
    cpf_mae = fields.String(load_default=None, allow_none=True, validate=validate_optional_cpf)

    endereco_casa = fields.Nested(EnderecoInputSchema, load_default=None, allow_none=True)


class AlunoResponseSchema(BaseSchema):
    id = fields.UUID()
    nome = fields.String()
    matricula = fields.String()
    escola = fields.String(attribute="instituicao.nome", dump_default=None)

    status = fields.String(attribute="status.value", dump_default=None)
    signup_completed_at = fields.DateTime(dump_default=None)


class AlunoListResponseSchema(BaseSchema):
    """Gestor views a list of Alunos (pagination)."""

    items = fields.List(fields.Nested(AlunoResponseSchema()), required=True)
    total = fields.Integer(required=True)
