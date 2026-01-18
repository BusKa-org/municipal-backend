from flask import request, jsonify
from flask_restx import Resource, Namespace
from app.services.auth_service import AuthService
from app.schemas.user_schema import UserCreateSchema

api = Namespace('auth', description='Authentication operations')
user_schema = UserCreateSchema()


@api.route('/register')
class Register(Resource):
    def post(self):
        json_data = request.get_json()
        
        errors = user_schema.validate(json_data)
        if errors:
            return {"error": "Validation failed", "details": errors}, 400
            
        return AuthService.register_user(json_data)

@api.route('/login')
class Login(Resource):
    def post(self):
        data = request.get_json()
        # Validação simples de login não precisa de schema complexo
        if not data.get('email') or not data.get('password'):
            return {"error": "Email and password required"}, 400
            
        return AuthService.login_user(data)
