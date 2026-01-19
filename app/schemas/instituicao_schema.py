from marshmallow import Schema, fields, validate

class EnderecoSchema(Schema):
    logradouro = fields.String(required=True)
    numero = fields.String(required=True)
    bairro = fields.String(required=True)
    cidade = fields.String(required=True)
    cep = fields.String(required=True)
    latitude = fields.Float(required=True, metadata={"description": "Latitude do local"})
    longitude = fields.Float(required=True, metadata={"description": "Longitude do local"})

class InstituicaoCreateSchema(Schema):
    nome = fields.String(required=True)
    cnpj = fields.String(required=True)
    tipo = fields.String(
        required=True, 
        validate=validate.OneOf([
            "INSTITUTO_FEDERAL", "UNIVERSIDADE_PUBLICA", "UNIVERSIDADE_PRIVADA",
            "ESCOLA_PUBLICA", "ESCOLA_PRIVADA", "ESCOLA_COMUNITARIA"
        ]),
        metadata={"description": "Tipo da instituição conforme modelo"}
    )
    endereco = fields.Nested(EnderecoSchema, required=True)

class InstituicaoResponseSchema(Schema):
    id = fields.String()
    nome = fields.String()
    cnpj = fields.String()
    tipo = fields.String()
    endereco = fields.Nested(EnderecoSchema, attribute="ponto.endereco")
    latitude = fields.Float(attribute="ponto.latitude")
    longitude = fields.Float(attribute="ponto.longitude")