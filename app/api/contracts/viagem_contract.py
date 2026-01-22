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
    
    from flask_restx import fields

    @staticmethod
    def criar_viagem_input(api):
        """Modelo para criar viagem manual (rota específica)"""
        return api.model('ViagemInput', {
            'rota_id': fields.String(required=True, description='UUID da Rota'),
            'data': fields.String(required=True, description='Data da viagem (YYYY-MM-DD)', example="2026-02-04")
        })

    @staticmethod
    def gerar_lote_input(api):
        """Modelo para o botão GERAR LOTE (apenas data)"""
        return api.model('GerarLoteInput', {
            'data': fields.String(required=True, description='Data para gerar as viagens (YYYY-MM-DD)', example="2026-02-04")
        })
        
    @staticmethod
    def confirmacao_input(api):
        """Modelo para o Aluno confirmar presença e escolher o ponto"""
        return api.model('ConfirmacaoInput', {
            'confirmacao': fields.Boolean(required=True, description='Confirmar (true) ou Cancelar (false)', example=True),
            'ponto_embarque_id': fields.String(required=False, description='UUID do Ponto de Embarque (Obrigatório se confirmação=true)', example="uuid-do-ponto")
        })    