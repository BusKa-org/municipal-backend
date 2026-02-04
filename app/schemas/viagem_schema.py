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

    acao = fields.String(required=True, validate=validate.OneOf(["INICIAR", "FINALIZAR"]))


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
    status = fields.Method("get_status")
    motorista_nome = fields.String(attribute="motorista.nome", dump_default="Sem Motorista")
    veiculo_placa = fields.String(attribute="veiculo.placa", dump_default="Sem Veículo")

    # Schedule info
    horario_inicio = fields.Method("get_horario_inicio")
    horario_fim = fields.DateTime(attribute="fim_real")
    inicio_real = fields.DateTime()  # Actual start time for elapsed calculation
    tipo = fields.Method("get_tipo")
    rota_id = fields.Method("get_rota_id")
    rota_nome = fields.Method("get_rota_nome")

    pontos = fields.List(fields.Nested(ViagemPontoResponseSchema), attribute="pontos_visitados")
    alunos = fields.List(fields.Nested(AlunoViagemResponseSchema), attribute="alunos_confirmados")

    # Counts for dashboard
    total_alunos = fields.Method("get_total_alunos")
    alunos_confirmados_count = fields.Method("get_alunos_confirmados_count")

    def get_total_alunos(self, obj):
        """Total students enrolled in the route."""
        if obj.horario_rota and obj.horario_rota.rota:
            return len(obj.horario_rota.rota.alunos_inscritos)
        return 0

    def get_alunos_confirmados_count(self, obj):
        """Number of students who confirmed presence."""
        if obj.alunos_confirmados:
            return sum(1 for a in obj.alunos_confirmados if a.confirmacao)
        return 0

    def get_status(self, obj):
        """Get status as string."""
        if obj.status:
            return obj.status.name if hasattr(obj.status, "name") else str(obj.status)
        return "AGENDADA"

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

    origem = fields.Method("get_origem")
    destino = fields.Method("get_destino")

    def get_origem(self, obj):
        if obj.horario_rota and obj.horario_rota.rota:
            rota = obj.horario_rota.rota
            if rota.pontos_padrao and len(rota.pontos_padrao) > 0:
                primeiro_ponto = sorted(rota.pontos_padrao, key=lambda p: p.ordem)[0]
                if primeiro_ponto.ponto:
                    return primeiro_ponto.ponto.apelido
        return None

    def get_destino(self, obj):
        if obj.horario_rota and obj.horario_rota.rota:
            rota = obj.horario_rota.rota
            if rota.pontos_padrao and len(rota.pontos_padrao) > 0:
                ultimo_ponto = sorted(rota.pontos_padrao, key=lambda p: p.ordem)[-1]
                if ultimo_ponto.ponto:
                    return ultimo_ponto.ponto.apelido
        return None
