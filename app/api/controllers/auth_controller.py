from flask import request
from flask_restx import Resource
from app.api.contracts.auth_contract import AuthContract
from app.services.auth_service import AuthService
from app.schemas.user_schema import UserCreateSchema

api = AuthContract.api
contract = AuthContract

user_schema = UserCreateSchema()

@api.route('/register')
class Register(Resource):
    @api.expect(contract.register_request)
    @api.doc(responses={
        201: 'Usuário criado com sucesso',
        400: 'Erro de validação ou dados duplicados'
    })
    def post(self):
        json_data = request.get_json()
        
        errors = user_schema.validate(json_data)
        if errors:
            return {"error": "Validation failed", "details": errors}, 400
            
        return AuthService.register_user(json_data)

@api.route('/login')
class Login(Resource):
    @api.expect(contract.login_request)
    @api.doc(responses={
        200: 'Login realizado com sucesso (Retorna Token)',
        400: 'Dados incompletos',
        401: 'Credenciais inválidas'
    })
    def post(self):
        data = request.get_json()
        if not data.get('email') or not data.get('password'):
            return {"error": "Email and password required"}, 400
            
        return AuthService.login_user(data)