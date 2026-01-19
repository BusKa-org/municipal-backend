from flask import request
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.onibus_service import OnibusService
from app.schemas.onibus_schema import OnibusCreateSchema, OnibusResponseSchema
from app.api.contracts.onibus_contract import OnibusContract

api = Namespace('onibus', description='Gerenciamento da Frota')

create_schema = OnibusCreateSchema()
response_schema = OnibusResponseSchema()
list_response_schema = OnibusResponseSchema(many=True)

onibus_model = OnibusContract.create_model(api)

@api.route('/')
class OnibusListResource(Resource):
    @api.doc('list_onibus')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self):
        """Lista a frota da prefeitura"""
        current_user_id = get_jwt_identity()
        onibus_list, status = OnibusService.list_all(current_user_id)
        
        if status != 200: return onibus_list, status
        
        return list_response_schema.dump(onibus_list), 200

    @api.doc('create_onibus')
    @api.expect(onibus_model)
    @api.expect(jwt_required=True)
    @jwt_required()
    def post(self):
        """Cadastra um novo ônibus"""
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validação Schema
        errors = create_schema.validate(data)
        if errors:
            return {"error": "Validation failed", "details": errors}, 400
            
        result, status = OnibusService.create_onibus(current_user_id, data)
        
        if status != 201: return result, status
        
        return response_schema.dump(result), 201

@api.route('/<string:id>')
class OnibusResource(Resource):
    @api.doc('get_onibus')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self, id):
        """Detalhes de um ônibus"""
        current_user_id = get_jwt_identity()
        result, status = OnibusService.get_by_id(current_user_id, id)
        
        if status != 200: return result, status
        return response_schema.dump(result), 200

    @api.doc('delete_onibus')
    @api.expect(jwt_required=True)
    @jwt_required()
    def delete(self, id):
        """Remove um ônibus"""
        current_user_id = get_jwt_identity()
        return OnibusService.delete_onibus(current_user_id, id)