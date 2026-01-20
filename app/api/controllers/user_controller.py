from flask import request
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.user_service import UserService
from app.schemas.user_schema import UserResponseSchema
from app.api.contracts.user_contract import UserContract

api = Namespace('users', description='Gerenciamento de Usuários e Perfil')

user_schema = UserResponseSchema()
user_list_schema = UserResponseSchema(many=True)

user_model = UserContract.user_response_model(api)
motorista_create_model = UserContract.motorista_create_model(api)
change_password_model = UserContract.change_password_model(api)

@api.route('')
class UserList(Resource):
    @api.doc('list_users')
    @api.expect(jwt_required=True)
    @jwt_required()
    @api.marshal_list_with(user_model)
    def get(self):
        """Lista todos os usuários (Apenas Gestor)"""
        users = UserService.get_all_users()
        return users

@api.route('/me')
class UserProfile(Resource):
    @api.doc('get_my_profile')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self):
        """Perfil do usuário logado"""
        current_user_id = get_jwt_identity()
        
        user = UserService.get_user_by_id(current_user_id)
        if not user:
            return {"error": "User not found"}, 404
            
        return user_schema.dump(user)

@api.route('/<string:id>')
@api.param('id', 'O UUID do usuário')
class UserResource(Resource):
    @api.doc('get_user_by_id')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self, id):
        """Busca usuário por ID"""
        user = UserService.get_user_by_id(id)
        if not user:
            return {"error": "User not found"}, 404
            
        return user_schema.dump(user)
    
@api.route('/motoristas')
class MotoristaCreateResource(Resource):
    @api.doc('create_motorista')
    @api.expect(motorista_create_model)
    @api.expect(jwt_required=True) 
    @jwt_required()
    def post(self):
        """Gestor cria um novo Motorista"""
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        return UserService.create_motorista(current_user_id, data)
    
@api.route('/change-password')
class UserChangePassword(Resource):
    @api.doc('change_user_password')
    @api.expect(change_password_model)
    @api.expect(jwt_required=True)
    @jwt_required()
    def post(self):
        """
        Altera a senha do usuário logado (Requer senha atual).
        Funciona para Gestor, Motorista e Aluno.
        """
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        return UserService.change_password(current_user_id, data)