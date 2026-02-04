from marshmallow import Schema, fields, validate

from app.schemas.endereco_schema import EnderecoInputSchema


class InstituicaoCreateSchema(Schema):
    nome = fields.String(required=True)
    cnpj = fields.String(required=True)
    tipo = fields.String(
        required=True,
        validate=validate.OneOf(
            [
                "INSTITUTO_FEDERAL",
                "UNIVERSIDADE_PUBLICA",
                "UNIVERSIDADE_PRIVADA",
                "ESCOLA_PUBLICA",
                "ESCOLA_PRIVADA",
                "ESCOLA_COMUNITARIA",
            ]
        ),
        metadata={"description": "Tipo da instituição conforme modelo"},
    )
    endereco = fields.Nested(EnderecoInputSchema, required=True)


class InstituicaoResponseSchema(Schema):
    id = fields.String()
    nome = fields.String()
    cnpj = fields.String()
    tipo = fields.String()
    endereco = fields.Nested(EnderecoInputSchema, attribute="ponto.endereco")
    latitude = fields.Float(attribute="ponto.latitude")
    longitude = fields.Float(attribute="ponto.longitude")
