from flask import request
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.viagens_service import ViagensService
from app.schemas.viagem_schema import ViagemCreateSchema, ViagemResponseSchema
from app.api.contracts.viagem_contract import ViagemContract

api = Namespace('viagens', description='Execução de Viagens')

create_schema = ViagemCreateSchema()
response_schema = ViagemResponseSchema()
list_response_schema = ViagemResponseSchema(many=True)

create_model = ViagemContract.create_model(api)
action_model = ViagemContract.action_model(api)
filter_parser = ViagemContract.filter_parser()

@api.route('/')
class ViagemListResource(Resource):
    
    @api.doc('list_all_viagens')
    @api.expect(filter_parser, validate=True)
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self):
        """Histórico completo de viagens com filtros (Apenas Gestor)"""
        user_id = get_jwt_identity()
        
        args = filter_parser.parse_args()
        
        result, status = ViagensService.list_viagens_gestor(user_id, args)
        
        if status != 200: return result, status
        
        return list_response_schema.dump(result), 200

    @api.doc('create_viagem')
    @api.expect(create_model, jwt_required=True)
    @jwt_required()
    def post(self):
        """Gera uma nova viagem manual (Gestor)"""
        user_id = get_jwt_identity()
        data = request.get_json()
        
        result, status = ViagensService.gerar_viagem(user_id, data)
        if status != 201: return result, status
        
        return result, 201

@api.route('/minhas')
class MinhasViagensResource(Resource):
    @api.doc('list_my_viagens')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self):
        """Lista viagens atribuídas ao motorista logado"""
        user_id = get_jwt_identity()
        result, status = ViagensService.list_viagens_motorista(user_id)
        
        if status != 200: return result, status

        return list_response_schema.dump(result), 200

@api.route('/<string:id>/acao')
class ViagemAcaoResource(Resource):
    @api.doc('control_viagem')
    @api.expect(action_model, jwt_required=True)
    @jwt_required()
    def put(self, id):
        """Controla a viagem (Iniciar, Finalizar, Registrar Ponto)"""
        user_id = get_jwt_identity()
        data = request.get_json()
        
        result, status = ViagensService.controlar_viagem(user_id, id, data)
        if status != 200: return result, status
        
        return response_schema.dump(result), 200