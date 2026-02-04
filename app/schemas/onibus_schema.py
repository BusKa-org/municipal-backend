from marshmallow import Schema, fields


class OnibusCreateSchema(Schema):
    placa = fields.String(required=True, metadata={"description": "Placa do veículo"})
    modelo = fields.String(required=False, metadata={"description": "Modelo do ônibus"})
    capacidade = fields.Integer(required=True, metadata={"description": "Capacidade total"})


class OnibusResponseSchema(Schema):
    id = fields.String()
    placa = fields.String()
    modelo = fields.String()
    capacidade = fields.Integer()
    prefeitura_id = fields.String()
