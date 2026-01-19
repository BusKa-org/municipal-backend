from flask_restx import fields

class OnibusContract:
    @staticmethod
    def create_model(api):
        return api.model('OnibusCreate', {
            'placa': fields.String(required=True, description='Placa do Veículo', example='ABC-1234'),
            'modelo': fields.String(description='Modelo/Marca', example='Mercedes-Benz OF-1721'),
            'capacidade': fields.Integer(required=True, description='Capacidade de passageiros', example=45)
        })