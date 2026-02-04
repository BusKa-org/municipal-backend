from marshmallow import Schema, fields


class EnderecoInputSchema(Schema):
    logradouro = fields.String(required=True)
    numero = fields.String(required=True)
    bairro = fields.String(required=True)
    cidade = fields.String(required=True)
    cep = fields.String(required=True)
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)
