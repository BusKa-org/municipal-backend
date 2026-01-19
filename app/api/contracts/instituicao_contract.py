from flask_restx import fields

class InstituicaoContract:
    @staticmethod
    def create_model(api):
        endereco_model = api.model('EnderecoInput', {
            'logradouro': fields.String(required=True, example='Rua das Flores'),
            'numero': fields.String(required=True, example='123'),
            'bairro': fields.String(required=True, example='Centro'),
            'cidade': fields.String(required=True, example='São Paulo'),
            'cep': fields.String(required=True, example='01001-000'),
            'latitude': fields.Float(required=True, example=-23.550520),
            'longitude': fields.Float(required=True, example=-46.633308)
        })

        return api.model('InstituicaoCreate', {
            'nome': fields.String(required=True, example='Escola Municipal 1'),
            'cnpj': fields.String(required=True, example='12345678000199'),
            'tipo': fields.String(
                required=True, 
                enum=[
                    'INSTITUTO_FEDERAL', 'UNIVERSIDADE_PUBLICA', 'UNIVERSIDADE_PRIVADA',
                    'ESCOLA_PUBLICA', 'ESCOLA_PRIVADA', 'ESCOLA_COMUNITARIA'
                ],
                description='Tipo da Instituição'
            ),
            'endereco': fields.Nested(endereco_model, required=True)
        })