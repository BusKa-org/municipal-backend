from marshmallow import Schema, fields

from .ponto_schema import PontoResponseSchema
from .horario_schema import HorarioResponseSchema


class RotaPontoResponseSchema(Schema):
    ordem = fields.Integer()
    ponto = fields.Nested(PontoResponseSchema)


class RotaResponseSchema(Schema):
    id = fields.String()
    nome = fields.String()
    motorista_id = fields.Method("get_motorista_id")
    veiculo_id = fields.Method("get_veiculo_id")
    prefeitura_id = fields.String()

    def get_motorista_id(self, obj):
        return str(obj.motorista_padrao_id) if obj.motorista_padrao_id else None

    def get_veiculo_id(self, obj):
        return str(obj.veiculo_padrao_id) if obj.veiculo_padrao_id else None


class RotaDetailResponseSchema(RotaResponseSchema):
    """Extended schema with nested relationships."""
    pontos = fields.Method("get_pontos")
    horarios = fields.Nested(HorarioResponseSchema, many=True, attribute="grade_horarios")

    def get_pontos(self, obj):
        return RotaPontoResponseSchema(many=True).dump(obj.pontos_padrao)
