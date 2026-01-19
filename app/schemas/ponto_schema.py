from marshmallow import Schema, fields

class PontoCreateSchema(Schema):
    apelido = fields.String(required=False, allow_none=True, metadata={"description": "Nome do ponto (ex: Escola A)"})
    latitude = fields.Float(required=True, metadata={"description": "Latitude"})
    longitude = fields.Float(required=True, metadata={"description": "Longitude"})

class PontoResponseSchema(Schema):
    id = fields.String()
    apelido = fields.String()
    latitude = fields.Float()
    longitude = fields.Float()
    endereco = fields.String(dump_default=None)
    instituicao = fields.String(dump_default=None)