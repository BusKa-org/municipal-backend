from marshmallow import Schema, fields

class ViagemCreateSchema(Schema):
    rota_id = fields.String(required=True, metadata={"description": "ID da Rota base"})
    data = fields.Date(required=True, metadata={"description": "Data da viagem (YYYY-MM-DD)"})

class ViagemPontoResponseSchema(Schema):
    ponto_id = fields.String()
    apelido = fields.String(attribute="ponto.apelido")
    ordem = fields.Integer()
    visitado = fields.Boolean()
    chegada_real = fields.DateTime()

class ViagemResponseSchema(Schema):
    id = fields.String()
    data = fields.Date()
    status = fields.String()
    motorista_nome = fields.String(attribute="motorista.nome", dump_default="Sem Motorista")
    veiculo_placa = fields.String(attribute="veiculo.placa", dump_default="Sem Veículo")
    
    pontos = fields.List(fields.Nested(ViagemPontoResponseSchema), attribute="pontos_visitados")