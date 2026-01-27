from flask import request
from flask_restx import Resource, Namespace

from app.services.auth_service import AuthService
from app.core.exceptions import ValidationError
from app.api.contracts import auth_contract

api = Namespace('auth', description='Autenticação')

# Register documentation models
models = auth_contract.register_models(api)


@api.route('/login')
class AuthLogin(Resource):
    @api.doc('auth_login')
    @api.expect(models['login_request'])
    @api.marshal_with(models['token_response'], code=200)
    def post(self):
        """Login (Gera o Token JWT)"""
        data = request.get_json() or {}
        
        if not data.get('email') or not data.get('password'):
            raise ValidationError("Email e senha são obrigatórios")
        
        return AuthService.login_user(data), 200