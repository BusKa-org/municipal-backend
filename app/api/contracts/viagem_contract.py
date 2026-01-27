"""Viagem endpoint documentation models."""

from flask_restx import fields


def register_models(api):
    """Register viagem models with the API namespace."""
    
    create_request = api.model('ViagemCreateRequest', {
        'rota_id': fields.String(required=True, description='UUID da rota'),
        'horario_id': fields.String(required=True, description='UUID do horário'),
        'data': fields.String(required=True, description='Data (YYYY-MM-DD)'),
        'motorista_id': fields.String(description='UUID do motorista (opcional)'),
        'veiculo_id': fields.String(description='UUID do veículo (opcional)')
    })
    
    lote_request = api.model('ViagemLoteRequest', {
        'data': fields.String(required=True, description='Data para gerar viagens (YYYY-MM-DD)')
    })
    
    confirmacao_request = api.model('ConfirmacaoRequest', {
        'ponto_embarque_id': fields.String(required=True, description='UUID do ponto de embarque')
    })
    
    acao_request = api.model('ViagemAcaoRequest', {
        'acao': fields.String(required=True, description='iniciar ou finalizar')
    })
    
    response = api.model('ViagemResponse', {
        'id': fields.String(description='UUID'),
        'data': fields.String(description='Data'),
        'horario_saida': fields.String(description='Horário'),
        'sentido': fields.String(description='Sentido'),
        'status': fields.String(description='AGENDADA, EM_ANDAMENTO, FINALIZADA'),
        'rota_id': fields.String(description='UUID da rota'),
        'rota_nome': fields.String(description='Nome da rota'),
        'motorista_id': fields.String(description='UUID do motorista'),
        'veiculo_id': fields.String(description='UUID do veículo')
    })
    
    ponto_embarque = api.model('PontoEmbarque', {
        'id': fields.String(description='UUID do ponto'),
        'apelido': fields.String(description='Nome'),
        'ordem': fields.Integer(description='Ordem na rota')
    })
    
    return {
        'create_request': create_request,
        'lote_request': lote_request,
        'confirmacao_request': confirmacao_request,
        'acao_request': acao_request,
        'response': response,
        'ponto_embarque': ponto_embarque
    }
