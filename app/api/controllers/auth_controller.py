from flask import request
from flask_restx import Resource, Namespace
from app.services.auth_service import AuthService
from app.api.contracts.auth_contract import AuthContract

api = Namespace('auth', description='Autenticação')

login_model = AuthContract.login_model(api)

@api.route('/login')
class AuthLogin(Resource):
    @api.doc('auth_login')
    @api.expect(login_model)
    def post(self):
        """Login (Gera o Token JWT)"""
        data = request.get_json()
        return AuthService.login_user(data)