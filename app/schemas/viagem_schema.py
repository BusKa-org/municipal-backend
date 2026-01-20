from marshmallow import Schema, fields

class AlunoViagemResponseSchema(Schema):
    aluno_id = fields.String()
    nome = fields.String(attribute="aluno.nome")
    confirmacao = fields.Boolean()
    ponto_embarque = fields.String(attribute="ponto_embarque.apelido")
    ponto_destino = fields.String(attribute="ponto_destino.apelido")

class ViagemCreateSchema(Schema):
    rota_id = fields.String(required=True, metadata={"description": "ID da Rota base"})
    data = fields.Date(required=True, metadata={"description": "Data da viagem (YYYY-MM-DD)"})
    horario_id = fields.String(required=False)

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
    
    alunos = fields.List(fields.Nested(AlunoViagemResponseSchema), attribute="alunos_confirmados")