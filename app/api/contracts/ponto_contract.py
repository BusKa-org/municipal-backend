"""Ponto endpoint documentation models."""

from flask_restx import fields


def register_models(api):
    """Register ponto models with the API namespace."""
    
    create_request = api.model('PontoCreateRequest', {
        'apelido': fields.String(description='Nome do ponto (ex: Escola A)'),
        'latitude': fields.Float(required=True, description='Latitude'),
        'longitude': fields.Float(required=True, description='Longitude')
    })
    
    response = api.model('PontoResponse', {
        'id': fields.String(description='UUID do ponto'),
        'apelido': fields.String(description='Nome/apelido'),
        'latitude': fields.Float(description='Latitude'),
        'longitude': fields.Float(description='Longitude'),
        'endereco': fields.String(description='Endereço formatado'),
        'instituicao': fields.String(description='Instituição vinculada')
    })
    
    return {
        'create_request': create_request,
        'response': response
    }
