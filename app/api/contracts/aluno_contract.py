from flask_restx import fields

class AlunoContract:

    @staticmethod
    def create_model(api):
        endereco_model = AlunoContract.endereco_model_gen(api)

        return api.model('AlunoCreate', {
            'nome': fields.String(required=True, description='Nome do Aluno'),
            'email': fields.String(required=True, description='Email de login'),
            'password': fields.String(required=True, description='Senha inicial'),
            'cpf': fields.String(required=True, description='CPF do Aluno'),
            'telefone': fields.String(description='Celular do Aluno'),

            'matricula': fields.String(required=True, description='Matrícula escolar'),
            'instituicao_id': fields.String(required=True, description='UUID da Instituição de ensino'),

            'nome_pai': fields.String(description='Nome do Pai'),
            'cpf_pai': fields.String(description='CPF do Pai'),
            'nome_mae': fields.String(description='Nome da Mãe'),
            'cpf_mae': fields.String(description='CPF da Mãe'),

            'endereco_casa': fields.Nested(
                endereco_model,
                required=True,
                description='Endereço residencial'
            )
        })

    @staticmethod
    def update_model(api):
        endereco_model = AlunoContract.endereco_model_gen(api)

        return api.model('AlunoUpdate', {
            'nome': fields.String(description='Nome do Aluno'),
            'telefone': fields.String(description='Celular do Aluno'),
            'matricula': fields.String(description='Matrícula escolar'),
            'nome_pai': fields.String(),
            'cpf_pai': fields.String(),
            'nome_mae': fields.String(),
            'cpf_mae': fields.String(),
            'endereco_casa': fields.Nested(
                endereco_model,
                description='Novo endereço residencial'
            )
        })

    @staticmethod
    def endereco_model_gen(api):
        return api.model('Endereco', {
            'logradouro': fields.String(description='Rua / Avenida'),
            'numero': fields.String(description='Número'),
            'bairro': fields.String(description='Bairro'),
            'cidade': fields.String(description='Cidade'),
            'cep': fields.String(description='CEP'),
            'latitude': fields.Float(description='Latitude'),
            'longitude': fields.Float(description='Longitude')
        })
