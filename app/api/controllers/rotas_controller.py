from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource

from app.api.contracts import rota_contract
from app.core.exceptions import ValidationError
from app.schemas.horario_schema import HorarioCreateSchema, HorarioResponseSchema
from app.schemas.rota_schema import (
    RotaCreateSchema,
    RotaDetailResponseSchema,
    RotaInscricaoSchema,
    RotaPontoAddSchema,
    RotaResponseSchema,
    RotaUpdateSchema,
)
from app.services import rotas_service

api = Namespace("rotas", description="Gestão de Rotas")

# API contracts (Swagger documentation)
models = rota_contract.register_models(api)

# Validation schemas (Marshmallow)
response_schema = RotaResponseSchema()
list_response_schema = RotaResponseSchema(many=True)
detail_response_schema = RotaDetailResponseSchema()
horario_create = HorarioCreateSchema()
horario_response = HorarioResponseSchema()
horario_list_response = HorarioResponseSchema(many=True)
create_schema = RotaCreateSchema()
update_schema = RotaUpdateSchema()
inscricao_schema = RotaInscricaoSchema()
ponto_add_schema = RotaPontoAddSchema()


@api.route("/")
class RotasListResource(Resource):
    @api.doc("list_rotas")
    @jwt_required()
    def get(self):
        """Lista todas as rotas disponíveis"""
        current_user_id = get_jwt_identity()
        rotas = rotas_service.list_all_rotas(current_user_id)
        return list_response_schema.dump(rotas), 200

    @api.doc("create_rota")
    @api.expect(models["create_request"])
    @jwt_required()
    def post(self):
        """Cria nova rota completa (Pontos + Horários + Dias)"""
        current_user_id = get_jwt_identity()
        data = request.get_json()

        errors = create_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        rota = rotas_service.create_rota(current_user_id, data)
        return {"message": "Rota criada com sucesso", "id": str(rota.id)}, 201


@api.route("/me")
class MyRotasResource(Resource):
    @api.doc("list_my_rotas")
    @jwt_required()
    def get(self):
        """Lista as rotas vinculadas ao usuário logado"""
        current_user_id = get_jwt_identity()
        rotas = rotas_service.list_my_rotas(current_user_id)
        return list_response_schema.dump(rotas), 200


@api.route("/<string:id>/inscricao")
@api.param("id", "UUID da Rota")
class RotaInscricaoResource(Resource):
    @api.doc("inscrever_aluno")
    @api.expect(models["inscricao_request"])
    @jwt_required()
    def post(self, id):
        """Aluno se inscreve ou remove inscrição na rota"""
        current_user_id = get_jwt_identity()
        data = request.get_json()

        errors = inscricao_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        result = rotas_service.gerenciar_inscricao_aluno(current_user_id, id, data)
        return result, 200


@api.route("/<string:id>/pontos")
class RotaPontosResource(Resource):
    @api.doc("add_pontos")
    @api.expect(models["ponto_input"])
    @jwt_required()
    def post(self, id):
        """Adiciona pontos geográficos à rota"""
        current_user_id = get_jwt_identity()
        data = request.get_json()

        errors = ponto_add_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        rotas_service.add_ponto(current_user_id, id, data)
        return {"message": "Pontos adicionados à rota com sucesso"}, 200


@api.route("/<string:id>/horarios")
class RotaHorariosResource(Resource):
    @api.doc("list_horarios")
    @api.marshal_list_with(models["horario_response"], code=200)
    @jwt_required()
    def get(self, id):
        """Lista a grade de horários de uma rota"""
        current_user = get_jwt_identity()
        horarios = rotas_service.get_horarios(current_user, id)
        return horario_list_response.dump(horarios), 200

    @api.doc("add_horario")
    @api.expect(models["horario_input"])
    @api.marshal_with(models["horario_response"], code=201)
    @jwt_required()
    def post(self, id):
        """Adiciona um horário de saída e dias de operação"""
        current_user = get_jwt_identity()
        data = request.get_json()

        errors = horario_create.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        horario = rotas_service.add_horario(current_user, id, data)
        return horario_response.dump(horario), 201


@api.route("/<string:id>")
class RotaResource(Resource):
    @api.doc("get_rota")
    @jwt_required()
    def get(self, id):
        """Obtém os detalhes de uma rota com pontos e horários"""
        current_user_id = get_jwt_identity()
        rota = rotas_service.get_by_id(current_user_id, id)
        return detail_response_schema.dump(rota), 200

    @api.doc("update_rota")
    @api.expect(models["create_request"])
    @jwt_required()
    def put(self, id):
        """Atualiza dados básicos da rota (Nome, Motorista, Veículo)"""
        current_user_id = get_jwt_identity()
        data = request.get_json()

        errors = update_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        rotas_service.update_rota(current_user_id, id, data)
        return {"message": "Rota atualizada com sucesso"}, 200

    @api.doc("delete_rota")
    @jwt_required()
    def delete(self, id):
        """Exclui uma rota"""
        current_user_id = get_jwt_identity()
        rotas_service.delete_rota(current_user_id, id)
        return {"message": "Rota removida com sucesso"}, 200
