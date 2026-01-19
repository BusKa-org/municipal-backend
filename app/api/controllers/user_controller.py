from flask import request
from flask_restx import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.user_service import UserService
from app.schemas.user_schema import UserResponseSchema

from app.api.contracts.user_contract import UserContract

api = UserContract.api
contract = UserContract

user_schema = UserResponseSchema()
user_list_schema = UserResponseSchema(many=True)

@api.route('')
class UserList(Resource):
    @api.doc('list_users')
    @api.expect(jwt_required=True)
    @jwt_required()
    @api.marshal_list_with(contract.user_response)
    def get(self):
        users = UserService.get_all_users()
        return user_list_schema.dump(users)

@api.route('/me')
class UserProfile(Resource):
    @api.doc('get_my_profile')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self):
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
        user = UserService.get_user_by_id(id)
        if not user:
            return {"error": "User not found"}, 404
            
        return user_schema.dump(user)
    
@api.route('/motoristas')
class MotoristaCreateResource(Resource):
    @api.doc('create_motorista')
    @api.expect(UserContract.motorista_create_model)
    @api.expect(jwt_required=True) 
    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        return UserService.create_motorista(current_user_id, data)