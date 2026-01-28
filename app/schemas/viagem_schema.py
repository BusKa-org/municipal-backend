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

    # Schedule info
    horario_inicio = fields.Method("get_horario_inicio")
    horario_fim = fields.DateTime(attribute="fim_real")
    tipo = fields.Method("get_tipo")
    rota_id = fields.Method("get_rota_id")
    rota_nome = fields.Method("get_rota_nome")

    pontos = fields.List(fields.Nested(ViagemPontoResponseSchema), attribute="pontos_visitados")
    alunos = fields.List(fields.Nested(AlunoViagemResponseSchema), attribute="alunos_confirmados")

    def get_horario_inicio(self, obj):
        if obj.horario_rota:
            return str(obj.horario_rota.horario_saida)
        return None

    def get_tipo(self, obj):
        if obj.horario_rota:
            return obj.horario_rota.sentido.name
        return None

    def get_rota_id(self, obj):
        if obj.horario_rota and obj.horario_rota.rota:
            return str(obj.horario_rota.rota.id)
        return None

    def get_rota_nome(self, obj):
        if obj.horario_rota and obj.horario_rota.rota:
            return obj.horario_rota.rota.nome
        return None
