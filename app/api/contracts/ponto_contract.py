from flask_restx import fields

class PontoContract:
    @staticmethod
    def create_model(api):
        return api.model('PontoCreate', {
            'apelido': fields.String(description='Nome amigável (Opcional)', example='Ponto da Praça'),
            'latitude': fields.Float(required=True, description='Latitude Geográfica', example=-23.550520),
            'longitude': fields.Float(required=True, description='Longitude Geográfica', example=-46.633308)
        })