from flask import request
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.user_service import UserService
from app.schemas.user_schema import UserResponseSchema, MotoristaCreateSchema, ChangePasswordSchema
from app.api.contracts import user_contract
from app.core.exceptions import ValidationError

api = Namespace('users', description='Gerenciamento de Usuários e Perfil')

# API contracts (Swagger documentation)
models = user_contract.register_models(api)

# Validation schemas (Marshmallow)
user_schema = UserResponseSchema()
list_response_schema = UserResponseSchema(many=True)
motorista_create_schema = MotoristaCreateSchema()
change_password_schema = ChangePasswordSchema()


@api.route('')
class UserList(Resource):
    @api.doc('list_users')
    @api.marshal_list_with(models['response'], code=200)
    @jwt_required()
    def get(self):
        """Lista todos os usuários (Apenas Gestor)"""
        users = UserService.get_all_users()
        return list_response_schema.dump(users), 200


@api.route('/me')
class UserProfile(Resource):
    @api.doc('get_my_profile')
    @api.marshal_with(models['response'], code=200)
    @jwt_required()
    def get(self):
        """Perfil do usuário logado"""
        current_user_id = get_jwt_identity()
        user = UserService.get_user_by_id(current_user_id)
        return user_schema.dump(user), 200


@api.route('/<string:id>')
@api.param('id', 'O UUID do usuário')
class UserResource(Resource):
    @api.doc('get_user_by_id')
    @jwt_required()
    def get(self, id):
        """Busca usuário por ID"""
        user = UserService.get_user_by_id(id)
        return user_schema.dump(user), 200


@api.route('/motoristas')
class MotoristaCreateResource(Resource):
    @api.doc('create_motorista')
    @api.expect(models['motorista_create'])
    @jwt_required()
    def post(self):
        """Gestor cria um novo Motorista"""
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        errors = motorista_create_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)
        
        motorista = UserService.create_motorista(current_user_id, data)
        return {"message": "Motorista cadastrado com sucesso", "id": str(motorista.usuario_id)}, 201


@api.route('/change-password')
class UserChangePassword(Resource):
    @api.doc('change_user_password')
    @api.expect(models['change_password'])
    @jwt_required()
    def post(self):
        """Altera a senha do usuário logado (Requer senha atual)."""
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        errors = change_password_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)
        
        UserService.change_password(current_user_id, data)
        return {"message": "Senha alterada com sucesso"}, 200