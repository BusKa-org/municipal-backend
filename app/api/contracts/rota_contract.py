from flask_restx import fields

class RotaContract:
    @staticmethod
    def ponto_model(api):
        return api.model('PontoRotaInput', {
            'latitude': fields.Float(required=True, example=-23.5505),
            'longitude': fields.Float(required=True, example=-46.6333),
            'ordem': fields.Integer(required=True, example=1),
            'apelido': fields.String(description='Nome opcional', example="Ponto da Praça")
        })

    @staticmethod
    def rota_input_model(api):
        horario = RotaContract.horario_model(api)
        ponto = RotaContract.ponto_model(api)

        return api.model('RotaCreateFull', {
            'nome': fields.String(required=True, description='Nome da Rota', example="Rota 101 - Centro"),
            'motorista_padrao_id': fields.String(description='UUID do Motorista Padrão (Opcional)', example="uuid-do-motorista"),
            'veiculo_padrao_id': fields.String(description='UUID do Veículo Padrão (Opcional)', example="uuid-do-onibus"),
            
            'pontos': fields.List(fields.Nested(ponto), description='Lista ordenada de pontos geográficos'),
            'horarios': fields.List(fields.Nested(horario), description='Grade de horários e dias de operação')
        })
        
            
    @staticmethod
    def horario_model(api):
        return api.model('HorarioInput', {
            'horario_saida': fields.String(required=True, description='Horário de saída (HH:MM)', example="07:00"),
            'sentido': fields.String(required=True, description='IDA ou VOLTA', enum=['IDA', 'VOLTA'], example="IDA"),
            'dias': fields.List(fields.String, required=True, 
                                description='Dias de operação', 
                                enum=['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM'],
                                example=["SEG", "QUA", "SEX"])
        })