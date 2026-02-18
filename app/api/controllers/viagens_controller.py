from typing import Any

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource

from app.api.contracts import viagem_contract
from app.schemas.viagem_schema import (
    ViagemAcaoRequestSchema,
    ViagemConfirmacaoRequestSchema,
    ViagemCreateRequestSchema,
    ViagemListQuerySchema,
    ViagemListResponseSchema,
    ViagemLoteRequestSchema,
    ViagemResponseSchema,
)
from app.services import viagens_service

api = Namespace("viagens", description="Execução de Viagens")

# API contracts (Swagger documentation)
models = viagem_contract.register_models(api)

# Validation schemas (Marshmallow)
viagem_response_schema = ViagemResponseSchema()
viagem_list_response_schema = ViagemListResponseSchema()

viagem_create_request_schema = ViagemCreateRequestSchema()
viagem_lote_request_schema = ViagemLoteRequestSchema()
viagem_confirmacao_request_schema = ViagemConfirmacaoRequestSchema()
viagem_acao_request_schema = ViagemAcaoRequestSchema()

viagem_list_query_schema = ViagemListQuerySchema()


@api.route("/aluno/agenda")
class AlunoAgendaResource(Resource):
    @api.doc("list_viagens_aluno")
    @api.response(200, "Success", models["viagem_list_response"])
    @jwt_required()
    def get(self) -> tuple[dict[str, Any], int]:
        user_id = get_jwt_identity()
        agenda = viagens_service.get_proximas_viagens_aluno(user_id)
        return (
            viagem_list_response_schema.dump(
                {
                    "items": agenda,
                    "total": len(agenda),
                }
            ),
            200,
        )


@api.route("/<string:id>/confirmacao")
class ViagemConfirmacaoResource(Resource):
    @api.doc("confirmar_presenca")
    @api.expect(models["viagem_confirmacao_request"])
    @api.response(200, "Success")
    @jwt_required()
    def put(self, id: str) -> tuple[dict[str, Any], int]:
        user_id = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        payload = viagem_confirmacao_request_schema.load(data)
        result = viagens_service.confirmar_presenca_aluno(user_id, id, payload)
        return result, 200


@api.route("/")
class ViagemListResource(Resource):
    @api.doc("list_all_viagens")
    @api.response(200, "Success", models["viagem_list_response"])
    @jwt_required()
    def get(self) -> tuple[dict[str, Any], int]:
        user_id = get_jwt_identity()
        data = request.args.to_dict()
        filters = viagem_list_query_schema.load(data)
        viagens = viagens_service.list_viagens_gestor(user_id, filters)
        return (
            viagem_list_response_schema.dump(
                {
                    "items": viagens,
                    "total": len(viagens),
                }
            ),
            200,
        )

    @api.doc("create_viagem")
    @api.expect(models["viagem_create_request"])
    @api.response(201, "Created", models["viagem_response"])
    @jwt_required()
    def post(self) -> tuple[dict[str, Any], int]:
        user_id = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        payload = viagem_create_request_schema.load(data)
        viagem = viagens_service.gerar_viagem(user_id, payload)
        return viagem_response_schema.dump(viagem), 201


@api.route("/gerar-lote")
class ViagemLoteResource(Resource):
    @api.doc("gerar_viagens_lote")
    @api.expect(models["viagem_lote_request"])
    @api.response(201, "Created")
    @jwt_required()
    def post(self) -> tuple[dict[str, Any], int]:
        user_id = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        payload = viagem_lote_request_schema.load(data)
        result = viagens_service.gerar_viagens_em_lote(user_id, payload["data"])
        return result, 201


@api.route("/minhas")
class MinhasViagensResource(Resource):
    @api.doc("list_my_viagens")
    @api.response(200, "Success", models["viagem_list_response"])
    @jwt_required()
    def get(self) -> tuple[dict[str, Any], int]:
        user_id = get_jwt_identity()
        viagens = viagens_service.list_viagens_motorista(user_id)
        return (
            viagem_list_response_schema.dump(
                {
                    "items": viagens,
                    "total": len(viagens),
                }
            ),
            200,
        )


@api.route("/<string:id>/acao")
class ViagemAcaoResource(Resource):
    @api.doc("control_viagem")
    @api.expect(models["viagem_acao_request"])
    @api.response(200, "Success", models["viagem_response"])
    @jwt_required()
    def put(self, id: str) -> tuple[dict[str, Any], int]:
        user_id = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        payload = viagem_acao_request_schema.load(data)
        viagem = viagens_service.controlar_viagem(user_id, id, payload)
        return viagem_response_schema.dump(viagem), 200
