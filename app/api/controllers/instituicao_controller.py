from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource

from app.api.contracts import instituicao_contract
from app.core.exceptions import ValidationError
from app.schemas.instituicao_schema import InstituicaoCreateSchema, InstituicaoResponseSchema
from app.services import instituicao_service

api = Namespace("instituicoes", description="Gestão de Escolas e Instituições de Ensino")

# API contracts (Swagger documentation)
models = instituicao_contract.register_models(api)

# Validation schemas (Marshmallow)
create_schema = InstituicaoCreateSchema()
response_schema = InstituicaoResponseSchema()
list_response_schema = InstituicaoResponseSchema(many=True)


@api.route("/public")
class InstituicaoPublicListResource(Resource):
    @api.doc("list_instituicoes_public")
    @api.marshal_list_with(models["response"], code=200)
    def get(self):
        """Lista todas as instituições (público - para cadastro de alunos)"""
        instituicoes = instituicao_service.list_all_public()
        return list_response_schema.dump(instituicoes), 200


@api.route("/")
class InstituicaoListResource(Resource):
    @api.doc("list_instituicoes")
    @api.marshal_list_with(models["response"], code=200)
    @jwt_required()
    def get(self):
        """Lista todas as instituições da prefeitura"""
        user_id = get_jwt_identity()
        instituicoes = instituicao_service.list_all(user_id)
        return list_response_schema.dump(instituicoes), 200

    @api.doc("create_instituicao")
    @api.expect(models["create_request"])
    @api.marshal_with(models["response"], code=201)
    @jwt_required()
    def post(self):
        """Cadastra uma nova instituição com endereço"""
        user_id = get_jwt_identity()
        data = request.get_json()

        errors = create_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        inst = instituicao_service.create_instituicao(user_id, data)
        return response_schema.dump(inst), 201


@api.route("/<string:id>")
class InstituicaoResource(Resource):
    @api.doc("get_instituicao")
    @api.marshal_with(models["response"], code=200)
    @jwt_required()
    def get(self, id):
        """Detalhes da instituição"""
        user_id = get_jwt_identity()
        inst = instituicao_service.get_by_id(user_id, id)
        return response_schema.dump(inst), 200

    @api.doc("delete_instituicao")
    @jwt_required()
    def delete(self, id):
        """Remove a instituição e seus vínculos"""
        user_id = get_jwt_identity()
        instituicao_service.delete_instituicao(user_id, id)
        return {"message": "Instituição removida com sucesso"}, 200
