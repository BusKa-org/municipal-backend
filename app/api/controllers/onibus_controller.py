from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource

from app.api.contracts import onibus_contract
from app.core.exceptions import ValidationError
from app.schemas.onibus_schema import OnibusCreateSchema, OnibusResponseSchema
from app.services import onibus_service

api = Namespace("onibus", description="Gerenciamento da Frota")

# API contracts (Swagger documentation)
models = onibus_contract.register_models(api)

# Validation schemas (Marshmallow)
create_schema = OnibusCreateSchema()
response_schema = OnibusResponseSchema()
list_response_schema = OnibusResponseSchema(many=True)


@api.route("/")
class OnibusListResource(Resource):
    @api.doc("list_onibus")
    @api.marshal_list_with(models["response"], code=200)
    @jwt_required()
    def get(self):
        """Lista a frota da prefeitura"""
        current_user_id = get_jwt_identity()
        onibus_list = onibus_service.list_all(current_user_id)
        return list_response_schema.dump(onibus_list), 200

    @api.doc("create_onibus")
    @api.expect(models["create_request"])
    @api.marshal_with(models["response"], code=201)
    @jwt_required()
    def post(self):
        """Cadastra um novo ônibus"""
        current_user_id = get_jwt_identity()
        data = request.get_json()

        errors = create_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        onibus = onibus_service.create_onibus(current_user_id, data)
        return response_schema.dump(onibus), 201


@api.route("/<string:id>")
class OnibusResource(Resource):
    @api.doc("get_onibus")
    @api.marshal_with(models["response"], code=200)
    @jwt_required()
    def get(self, id):
        """Detalhes de um ônibus"""
        current_user_id = get_jwt_identity()
        onibus = onibus_service.get_by_id(current_user_id, id)
        return response_schema.dump(onibus), 200

    @api.doc("delete_onibus")
    @jwt_required()
    def delete(self, id):
        """Remove um ônibus"""
        current_user_id = get_jwt_identity()
        onibus_service.delete_onibus(current_user_id, id)
        return {"message": "Ônibus removido com sucesso"}, 200
