"""Onibus endpoint documentation models."""

from flask_restx import fields


def register_models(api):
    """Register onibus models with the API namespace."""
    
    create_request = api.model('OnibusCreateRequest', {
        'placa': fields.String(required=True, description='Placa do veículo'),
        'modelo': fields.String(description='Modelo'),
        'capacidade': fields.Integer(description='Capacidade de passageiros'),
        'ano': fields.Integer(description='Ano de fabricação')
    })
    
    response = api.model('OnibusResponse', {
        'id': fields.String(description='UUID do ônibus'),
        'placa': fields.String(description='Placa'),
        'modelo': fields.String(description='Modelo'),
        'capacidade': fields.Integer(description='Capacidade'),
        'ano': fields.Integer(description='Ano')
    })
    
    return {
        'create_request': create_request,
        'response': response
    }
