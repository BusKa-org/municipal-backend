"""Rota endpoint documentation models."""

from flask_restx import fields


def register_models(api):
    """Register rota models with the API namespace."""
    
    horario_input = api.model('HorarioInput', {
        'horario_saida': fields.String(required=True, description='Horário (HH:MM)'),
        'sentido': fields.String(required=True, description='IDA, VOLTA ou CIRCULAR'),
        'dias': fields.List(fields.String, required=True, description='Dias da semana (SEG, TER, ...)')
    })
    
    ponto_input = api.model('RotaPontoInput', {
        'ponto_id': fields.String(required=True, description='UUID do ponto'),
        'ordem': fields.Integer(required=True, description='Ordem na rota')
    })
    
    create_request = api.model('RotaCreateRequest', {
        'nome': fields.String(required=True, description='Nome da rota'),
        'motorista_padrao_id': fields.String(description='UUID do motorista padrão'),
        'veiculo_padrao_id': fields.String(description='UUID do veículo padrão'),
        'pontos': fields.List(fields.Nested(ponto_input), description='Pontos da rota'),
        'horarios': fields.List(fields.Nested(horario_input), description='Grade de horários')
    })
    
    response = api.model('RotaResponse', {
        'id': fields.String(description='UUID'),
        'nome': fields.String(description='Nome'),
        'motorista_id': fields.String(description='UUID do motorista padrão'),
        'veiculo_id': fields.String(description='UUID do veículo padrão'),
        'prefeitura_id': fields.String(description='UUID da prefeitura')
    })
    
    inscricao_request = api.model('InscricaoRequest', {
        'acao': fields.String(required=True, description='inscrever ou desinscrever')
    })
    
    horario_response = api.model('HorarioResponse', {
        'id': fields.String(description='UUID'),
        'horario_saida': fields.String(description='Horário'),
        'sentido': fields.String(description='Sentido'),
        'dias': fields.List(fields.String, description='Dias')
    })
    
    return {
        'create_request': create_request,
        'response': response,
        'inscricao_request': inscricao_request,
        'horario_input': horario_input,
        'horario_response': horario_response,
        'ponto_input': ponto_input
    }
