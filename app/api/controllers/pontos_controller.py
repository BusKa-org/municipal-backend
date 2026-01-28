from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource

from app.api.contracts import ponto_contract
from app.core.exceptions import ValidationError
from app.schemas.ponto_schema import PontoCreateSchema, PontoResponseSchema, PontoUpdateSchema
from app.services import pontos_service

api = Namespace("pontos", description="Gestão de Infraestrutura Geográfica")

# API contracts (Swagger documentation)
models = ponto_contract.register_models(api)

# Validation schemas (Marshmallow)
create_schema = PontoCreateSchema()
update_schema = PontoUpdateSchema()
response_schema = PontoResponseSchema()
list_response_schema = PontoResponseSchema(many=True)


@api.route("/")
class PontosListResource(Resource):
    @api.doc("list_pontos", responses={200: ("Success", [models["response"]])})
    @jwt_required()
    def get(self):
        """Lista todos os pontos da prefeitura"""
        user_id = get_jwt_identity()
        pontos = pontos_service.list_all(user_id)
        return list_response_schema.dump(pontos), 200

    @api.doc("create_ponto")
    @api.expect(models["create_request"])
    @api.marshal_with(models["response"], code=201)
    @jwt_required()
    def post(self):
        """Cria um novo ponto geográfico"""
        user_id = get_jwt_identity()
        data = request.get_json()

        errors = create_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        ponto = pontos_service.create_ponto(user_id, data)
        return response_schema.dump(ponto), 201


@api.route("/<string:id>")
class PontoResource(Resource):
    @api.doc("get_ponto")
    @api.marshal_with(models["response"], code=200)
    @jwt_required()
    def get(self, id):
        """Detalhes de um ponto"""
        user_id = get_jwt_identity()
        ponto = pontos_service.get_by_id(user_id, id)
        return response_schema.dump(ponto), 200

    @api.doc("update_ponto")
    @api.expect(models["create_request"])
    @api.marshal_with(models["response"], code=200)
    @jwt_required()
    def put(self, id):
        """Atualiza apelido ou coordenadas de um ponto"""
        user_id = get_jwt_identity()
        data = request.get_json()

        errors = update_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        ponto = pontos_service.update_ponto(user_id, id, data)
        return response_schema.dump(ponto), 200

    @api.doc("delete_ponto")
    @jwt_required()
    def delete(self, id):
        """Exclui um ponto (se não estiver em uso)"""
        user_id = get_jwt_identity()
        pontos_service.delete_ponto(user_id, id)
        return {"message": "Ponto removido com sucesso"}, 200
