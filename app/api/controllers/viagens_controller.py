from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, reqparse

from app.api.contracts import viagem_contract
from app.core.exceptions import ValidationError
from app.schemas.viagem_schema import (
    ViagemAcaoSchema,
    ViagemConfirmacaoSchema,
    ViagemCreateSchema,
    ViagemLoteSchema,
    ViagemResponseSchema,
)
from app.services import viagens_service

api = Namespace("viagens", description="Execução de Viagens")

# API contracts (Swagger documentation)
models = viagem_contract.register_models(api)

# Validation schemas (Marshmallow)
response_schema = ViagemResponseSchema()
list_response_schema = ViagemResponseSchema(many=True)
create_schema = ViagemCreateSchema()
lote_schema = ViagemLoteSchema()
confirmacao_schema = ViagemConfirmacaoSchema()
acao_schema = ViagemAcaoSchema()

# Filter parser for gestor listing
filter_parser = reqparse.RequestParser()
filter_parser.add_argument(
    "data_inicio", type=str, required=False, help="Filtro data inicial (YYYY-MM-DD)"
)
filter_parser.add_argument(
    "data_fim", type=str, required=False, help="Filtro data final (YYYY-MM-DD)"
)
filter_parser.add_argument(
    "status",
    type=str,
    required=False,
    choices=("AGENDADA", "EM_ANDAMENTO", "FINALIZADA"),
    help="Status da viagem",
)
filter_parser.add_argument("motorista_id", type=str, required=False, help="UUID do motorista")
filter_parser.add_argument("rota_id", type=str, required=False, help="UUID da rota")


@api.route("/aluno/agenda")
class AlunoAgendaResource(Resource):
    @api.doc("list_viagens_aluno")
    @jwt_required()
    def get(self):
        """Lista as próximas viagens do aluno para confirmar presença."""
        user_id = get_jwt_identity()
        agenda = viagens_service.get_proximas_viagens_aluno(user_id)
        return agenda, 200


@api.route("/<string:id>/pontos-embarque")
class ViagemPontosResource(Resource):
    @api.doc("list_pontos_embarque_viagem")
    @api.marshal_list_with(models["ponto_embarque"], code=200)
    @jwt_required()
    def get(self, id):
        """Lista todos os pontos de embarque disponíveis para esta viagem."""
        user_id = get_jwt_identity()
        pontos = viagens_service.listar_pontos_embarque(user_id, id)
        return pontos, 200


@api.route("/<string:id>/confirmacao")
class ViagemConfirmacaoResource(Resource):
    @api.doc("confirmar_presenca")
    @api.expect(models["confirmacao_request"])
    @jwt_required()
    def put(self, id):
        """Aluno confirma presença na viagem e seleciona ponto de embarque."""
        user_id = get_jwt_identity()
        data = request.get_json()

        errors = confirmacao_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        result = viagens_service.confirmar_presenca_aluno(user_id, id, data)
        return result, 200


@api.route("/")
class ViagemListResource(Resource):

    @api.doc("list_all_viagens")
    @api.expect(filter_parser, validate=True)
    @api.marshal_list_with(models["response"], code=200)
    @jwt_required()
    def get(self):
        """Histórico completo de viagens com filtros (Apenas Gestor)"""
        user_id = get_jwt_identity()
        args = filter_parser.parse_args()
        viagens = viagens_service.list_viagens_gestor(user_id, args)
        return list_response_schema.dump(viagens), 200

    @api.doc("create_viagem")
    @api.expect(models["create_request"])
    @jwt_required()
    def post(self):
        """Gera uma nova viagem manual (Gestor)"""
        user_id = get_jwt_identity()
        data = request.get_json()

        errors = create_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        result = viagens_service.gerar_viagem(user_id, data)
        return result, 201


@api.route("/gerar-lote")
class ViagemLoteResource(Resource):

    @api.doc("gerar_viagens_lote")
    @api.expect(models["lote_request"])
    @jwt_required()
    def post(self):
        """Gera viagens em lote para TODAS as rotas da prefeitura no dia especificado."""
        user_id = get_jwt_identity()
        data = request.get_json()

        errors = lote_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        result = viagens_service.gerar_viagens_em_lote(user_id, data["data"])
        return result, 201


@api.route("/minhas")
class MinhasViagensResource(Resource):
    @api.doc("list_my_viagens")
    @api.marshal_list_with(models["response"], code=200)
    @jwt_required()
    def get(self):
        """Lista viagens atribuídas ao motorista logado"""
        user_id = get_jwt_identity()
        viagens = viagens_service.list_viagens_motorista(user_id)
        return list_response_schema.dump(viagens), 200


@api.route("/<string:id>/acao")
class ViagemAcaoResource(Resource):
    @api.doc("control_viagem")
    @api.expect(models["acao_request"])
    @api.marshal_with(models["response"], code=200)
    @jwt_required()
    def put(self, id):
        """Controla a viagem (Iniciar, Finalizar)"""
        user_id = get_jwt_identity()
        data = request.get_json()

        errors = acao_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        viagem = viagens_service.controlar_viagem(user_id, id, data)
        return response_schema.dump(viagem), 200
