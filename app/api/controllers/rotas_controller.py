from flask import request
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.rotas_service import RotasService
from app.api.contracts.rota_contract import RotaContract
from app.schemas.horario_schema import HorarioCreateSchema, HorarioResponseSchema

horario_create = HorarioCreateSchema()
horario_response = HorarioResponseSchema()
horario_list_response = HorarioResponseSchema(many=True)
api = Namespace('rotas', description='Gestão de Rotas')

rota_model = RotaContract.create_model(api)
horario_model = RotaContract.horario_model(api)

@api.route('/')
class RotasListResource(Resource):
    @api.doc('list_rotas')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self):
        """Lista todas as rotas disponíveis na prefeitura"""
        current_user_id = get_jwt_identity()
        return RotasService.list_all_rotas(current_user_id)

    @api.doc('create_rota')
    @api.expect(rota_model, jwt_required=True)
    @jwt_required()
    def post(self):
        """Cria uma nova rota"""
        current_user_id = get_jwt_identity()
        data = request.get_json()
        return RotasService.create_rota(current_user_id, data)

@api.route('/me')
class MyRotasResource(Resource):
    @api.doc('list_my_rotas')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self):
        """Lista as rotas vinculadas ao usuário logado"""
        current_user_id = get_jwt_identity()
        return RotasService.list_my_rotas(current_user_id)

@api.route('/<string:id>/inscricao')
class RotaInscricaoResource(Resource):
    @api.doc('inscrever_rota')
    @api.expect(jwt_required=True)
    @jwt_required()
    def put(self, id):
        """Inscrever ou desinscrever aluno na rota"""
        current_user_id = get_jwt_identity()
        return RotasService.inscricao_aluno_rota(current_user_id, id)

@api.route('/<string:id>/pontos')
class RotaPontosResource(Resource):
    @api.doc('add_pontos')
    @api.expect(jwt_required=True)
    @jwt_required()
    def post(self, id):
        """Adiciona pontos geográficos à rota"""
        current_user_id = get_jwt_identity()
        data = request.get_json()
        return RotasService.add_ponto(current_user_id, id, data)

@api.route('/<string:id>/horarios')
class RotaHorariosResource(Resource):
    @api.doc('list_horarios')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self, id):
        """Lista a grade de horários de uma rota"""
        if not horario_list_response: return {"error": "Schema not configured"}, 500
        
        current_user = get_jwt_identity()
        result, status = RotasService.get_horarios(current_user, id)
        if status != 200: return result, status
        
        return horario_list_response.dump(result), 200

    @api.doc('add_horario')
    @api.expect(horario_model, jwt_required=True)
    @jwt_required()
    def post(self, id):
        """Adiciona um horário de saída e dias de operação"""
        if not horario_create: return {"error": "Schema not configured"}, 500

        current_user = get_jwt_identity()
        data = request.get_json()
        
        errors = horario_create.validate(data)
        if errors: return {"error": "Validation error", "details": errors}, 400
        
        result, status = RotasService.add_horario(current_user, id, data)
        if status != 201: return result, status
        
        return horario_response.dump(result), 201
    

@api.route('/<string:id>')
class RotaResource(Resource):
    @api.doc('get_rota')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self, id):
        """Obtém os detalhes de uma rota"""
        current_user_id = get_jwt_identity()
        return RotasService.get_by_id(current_user_id, id)

    @api.doc('update_rota')
    @api.expect(rota_model, jwt_required=True)
    @jwt_required()
    def put(self, id):
        """Atualiza dados básicos da rota (Nome, Motorista, Veículo)"""
        current_user_id = get_jwt_identity()
        data = request.get_json()
        return RotasService.update_rota(current_user_id, id, data)

    @api.doc('delete_rota')
    @api.expect(jwt_required=True)
    @jwt_required()
    def delete(self, id):
        """Exclui uma rota"""
        current_user_id = get_jwt_identity()
        return RotasService.delete_rota(current_user_id, id)
