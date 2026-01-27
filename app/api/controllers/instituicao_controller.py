from flask import request
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.instituicao_service import InstituicaoService
from app.schemas.instituicao_schema import InstituicaoCreateSchema, InstituicaoResponseSchema
from app.core.exceptions import ValidationError
from app.api.contracts import instituicao_contract

api = Namespace('instituicoes', description='Gestão de Escolas e Instituições de Ensino')

# API contracts (Swagger documentation)
models = instituicao_contract.register_models(api)

# Validation schemas (Marshmallow)
create_schema = InstituicaoCreateSchema()
response_schema = InstituicaoResponseSchema()
list_response_schema = InstituicaoResponseSchema(many=True)


@api.route('/')
class InstituicaoListResource(Resource):
    @api.doc('list_instituicoes')
    @api.marshal_list_with(models['response'], code=200)
    @jwt_required()
    def get(self):
        """Lista todas as instituições da prefeitura"""
        user_id = get_jwt_identity()
        instituicoes = InstituicaoService.list_all(user_id)
        return list_response_schema.dump(instituicoes), 200

    @api.doc('create_instituicao')
    @api.expect(models['create_request'])
    @api.marshal_with(models['response'], code=201)
    @jwt_required()
    def post(self):
        """Cadastra uma nova instituição com endereço"""
        user_id = get_jwt_identity()
        data = request.get_json()
        
        errors = create_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)
        
        inst = InstituicaoService.create_instituicao(user_id, data)
        return response_schema.dump(inst), 201


@api.route('/<string:id>')
class InstituicaoResource(Resource):
    @api.doc('get_instituicao')
    @api.marshal_with(models['response'], code=200)
    @jwt_required()
    def get(self, id):
        """Detalhes da instituição"""
        user_id = get_jwt_identity()
        inst = InstituicaoService.get_by_id(user_id, id)
        return response_schema.dump(inst), 200

    @api.doc('delete_instituicao')
    @jwt_required()
    def delete(self, id):
        """Remove a instituição e seus vínculos"""
        user_id = get_jwt_identity()
        InstituicaoService.delete_instituicao(user_id, id)
        return {"message": "Instituição removida com sucesso"}, 200