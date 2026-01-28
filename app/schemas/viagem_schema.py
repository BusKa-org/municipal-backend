from marshmallow import Schema, fields, validate

# ==========================================
# Input Schemas (Validation)
# ==========================================


class ViagemCreateSchema(Schema):
    """Schema for creating a new trip."""

    rota_id = fields.String(required=True)
    horario_id = fields.String(required=True)
    data = fields.Date(required=True)
    motorista_id = fields.String(load_default=None)
    veiculo_id = fields.String(load_default=None)


class ViagemLoteSchema(Schema):
    """Schema for batch trip generation."""

    data = fields.String(required=True)


class ViagemConfirmacaoSchema(Schema):
    """Schema for student trip confirmation."""

    confirmacao = fields.Boolean(required=True)
    ponto_embarque_id = fields.String(load_default=None)


class ViagemAcaoSchema(Schema):
    """Schema for trip control actions."""

    acao = fields.String(required=True, validate=validate.OneOf(["iniciar", "finalizar"]))


# ==========================================
# Response Schemas (Serialization)
# ==========================================


class AlunoViagemResponseSchema(Schema):
    aluno_id = fields.String()
    nome = fields.String(attribute="aluno.nome")
    confirmacao = fields.Boolean()
    ponto_embarque = fields.String(attribute="ponto_embarque.apelido")
    ponto_destino = fields.String(attribute="ponto_destino.apelido")


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
