from flask_restx import fields

class UserContract:
    
    @staticmethod
    def user_response_model(api):
        return api.model('UserResponse', {
            'id': fields.String(description='ID único UUID'),
            'nome': fields.String(description='Nome completo'),
            'email': fields.String(description='Email'),
            'prefeitura_id': fields.String(description='UUID da Prefeitura'),
            'cpf': fields.String(description='CPF'),
            'telefone': fields.String(description='Telefone'),
            'role': fields.String(description='Perfil de acesso'),        
            'matricula': fields.String(description='Matrícula escolar'),
            'nome_pai': fields.String(description='Nome do Pai (Apenas Aluno)'),
            'nome_mae': fields.String(description='Nome da Mãe (Apenas Aluno)'),
            'cnh': fields.String(description='Número da CNH (Apenas Motorista)'),
            'salario': fields.Float(description='Salário (Apenas Gestor)')
        })
    
    @staticmethod
    def motorista_create_model(api):
        return api.model('MotoristaCreate', {
            'nome': fields.String(required=True, example='João Motorista'),
            'email': fields.String(required=True, example='motorista@email.com'),
            'password': fields.String(required=True, example='senha123'),
            'cpf': fields.String(required=True, example='11122233344'),
            'cnh': fields.String(required=True, description='CNH Obrigatória', example='12345678900'),
            'telefone': fields.String(required=True, example='11999999999')
        })