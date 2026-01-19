from flask_restx import fields

class RotaContract:
    @staticmethod
    def create_model(api):
        return api.model('RotaCreate', {
            'nome': fields.String(required=True, example='Rota Universitária Manhã'),
            'motorista_id': fields.String(description='UUID do Motorista Padrão'),
            'veiculo_id': fields.String(description='UUID do Ônibus Padrão')
        })

    @staticmethod
    def horario_model(api):
        return api.model('HorarioCreate', {
            'horario_saida': fields.String(required=True, example='07:30', description='Formato HH:MM'),
            'sentido': fields.String(required=True, enum=['IDA', 'VOLTA', 'CIRCULAR']),
            'dias': fields.List(fields.String(enum=['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM']), required=True)
        })