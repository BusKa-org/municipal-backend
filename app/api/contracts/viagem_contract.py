from flask_restx import fields, reqparse

class ViagemContract:
    @staticmethod
    def create_model(api):
        return api.model('ViagemCreate', {
            'rota_id': fields.String(required=True, description='UUID da Rota'),
            'data': fields.String(required=True, description='Data YYYY-MM-DD', example='2026-01-20')
        })

    @staticmethod
    def action_model(api):
        return api.model('ViagemAction', {
            'acao': fields.String(required=True, enum=['INICIAR', 'FINALIZAR', 'REGISTRAR_PONTO'], description='Ação a executar'),
            'ponto_id': fields.String(description='Obrigatório se acao=REGISTRAR_PONTO')
        })
    
    @staticmethod
    def filter_parser():
        parser = reqparse.RequestParser()
        parser.add_argument('data_inicio', type=str, required=False, help='Filtro data inicial (YYYY-MM-DD)')
        parser.add_argument('data_fim', type=str, required=False, help='Filtro data final (YYYY-MM-DD)')
        parser.add_argument('status', type=str, required=False, choices=('AGENDADA', 'EM_ANDAMENTO', 'FINALIZADA'), help='Status da viagem')
        parser.add_argument('motorista_id', type=str, required=False, help='UUID do motorista')
        parser.add_argument('rota_id', type=str, required=False, help='UUID da rota')
        return parser