from flask import request
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.instituicao_service import InstituicaoService
from app.schemas.instituicao_schema import InstituicaoCreateSchema, InstituicaoResponseSchema
from app.api.contracts.instituicao_contract import InstituicaoContract

api = Namespace('instituicoes', description='Gestão de Escolas e Instituições de Ensino')

create_schema = InstituicaoCreateSchema()
response_schema = InstituicaoResponseSchema()
list_response_schema = InstituicaoResponseSchema(many=True)

create_model = InstituicaoContract.create_model(api)

@api.route('/')
class InstituicaoListResource(Resource):
    @api.doc('list_instituicoes')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self):
        """Lista todas as instituições da prefeitura"""
        user_id = get_jwt_identity()
        result, status = InstituicaoService.list_all(user_id)
        
        if status != 200: return result, status
        return list_response_schema.dump(result), 200

    @api.doc('create_instituicao')
    @api.expect(create_model, jwt_required=True)
    @jwt_required()
    def post(self):
        """Cadastra uma nova instituição com endereço"""
        user_id = get_jwt_identity()
        data = request.get_json()
        
        errors = create_schema.validate(data)
        if errors: return {"error": "Validation error", "details": errors}, 400
        
        result, status = InstituicaoService.create_instituicao(user_id, data)
        
        if status != 201: return result, status
        return response_schema.dump(result), 201

@api.route('/<string:id>')
class InstituicaoResource(Resource):
    @api.doc('get_instituicao')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self, id):
        """Detalhes da instituição"""
        user_id = get_jwt_identity()
        result, status = InstituicaoService.get_by_id(user_id, id)
        
        if status != 200: return result, status
        return response_schema.dump(result), 200

    @api.doc('delete_instituicao')
    @api.expect(jwt_required=True)
    @jwt_required()
    def delete(self, id):
        """Remove a instituição e seus vínculos"""
        user_id = get_jwt_identity()
        return InstituicaoService.delete_instituicao(user_id, id)