"""Auth endpoint documentation models."""

from flask_restx import fields


def register_models(api):
    """Register auth models with the API namespace."""
    
    login_request = api.model('LoginRequest', {
        'email': fields.String(required=True, description='Email do usuário'),
        'password': fields.String(required=True, description='Senha')
    })
    
    token_response = api.model('TokenResponse', {
        'access_token': fields.String(description='JWT Token'),
        'token_type': fields.String(description='Tipo (Bearer)')
    })
    
    return {
        'login_request': login_request,
        'token_response': token_response
    }
