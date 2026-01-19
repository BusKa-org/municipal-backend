from flask import request
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.pontos_service import PontosService
from app.schemas.ponto_schema import PontoCreateSchema, PontoResponseSchema
from app.api.contracts.ponto_contract import PontoContract

api = Namespace('pontos', description='Gestão de Infraestrutura Geográfica')

create_schema = PontoCreateSchema()
response_schema = PontoResponseSchema()
list_response_schema = PontoResponseSchema(many=True)

ponto_model = PontoContract.create_model(api)

@api.route('/')
class PontosListResource(Resource):
    @api.doc('list_pontos')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self):
        """Lista todos os pontos da prefeitura"""
        user_id = get_jwt_identity()
        result, status = PontosService.list_all(user_id)
        
        if status != 200: return result, status
        
        return list_response_schema.dump(result), 200

    @api.doc('create_ponto')
    @api.expect(ponto_model, jwt_required=True)
    @jwt_required()
    def post(self):
        """Cria um novo ponto geográfico"""
        user_id = get_jwt_identity()
        data = request.get_json()
        
        errors = create_schema.validate(data)
        if errors:
            return {"error": "Validation failed", "details": errors}, 400
            
        result, status = PontosService.create_ponto(user_id, data)
        
        if status != 201: return result, status
        
        return response_schema.dump(result), 201

@api.route('/<string:id>')
class PontoResource(Resource):
    @api.doc('get_ponto')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self, id):
        """Detalhes de um ponto"""
        user_id = get_jwt_identity()
        result, status = PontosService.get_by_id(user_id, id)
        
        if status != 200: return result, status
        return response_schema.dump(result), 200

    @api.doc('update_ponto')
    @api.expect(ponto_model, jwt_required=True)
    @jwt_required()
    def put(self, id):
        """Atualiza apelido ou coordenadas de um ponto"""
        user_id = get_jwt_identity()
        data = request.get_json()
        
        result, status = PontosService.update_ponto(user_id, id, data)
        
        if status != 200: return result, status
        return response_schema.dump(result), 200

    @api.doc('delete_ponto')
    @api.expect(jwt_required=True)
    @jwt_required()
    def delete(self, id):
        """Exclui um ponto (se não estiver em uso)"""
        user_id = get_jwt_identity()
        return PontosService.delete_ponto(user_id, id)