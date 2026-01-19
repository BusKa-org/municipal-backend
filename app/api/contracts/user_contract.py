from flask_restx import Namespace, fields

class UserContract:
    api = Namespace('users', description='Gerenciamento de Usuários e Perfil')

    user_response = api.model('UserResponse', {
        'id': fields.String(description='ID único UUID'),
        'nome': fields.String(description='Nome completo'),
        'email': fields.String(description='Email'),
        'prefeitura_id': fields.String(
                required=True, 
                description='UUID da Prefeitura', 
                example='5d241870-a556-41f8-bbb3-3b168d7ff0c8'
        ),
        'cpf': fields.String(description='CPF'),
        'telefone': fields.String(description='Telefone'),
        'role': fields.String(
                description='Perfil de acesso', 
                enum=['ALUNO', 'MOTORISTA', 'GESTOR'],
                example='ALUNO'
            ),        
        'matricula': fields.String(description='Matrícula escolar'),
        'nome_pai': fields.String(description='Nome do Pai (Apenas Aluno)'),
        'nome_mae': fields.String(description='Nome da Mãe (Apenas Aluno)'),
        
        'cnh': fields.String(description='Número da CNH (Apenas Motorista)'),
        
        'salario': fields.Float(description='Salário (Apenas Gestor)')
    })
    
    motorista_create_model = api.model('MotoristaCreate', {
        'nome': fields.String(required=True, example='João Motorista'),
        'email': fields.String(required=True, example='motorista@email.com'),
        'password': fields.String(required=True, example='senha123'),
        'cpf': fields.String(required=True, example='11122233344'),
        'cnh': fields.String(required=True, description='CNH Obrigatória', example='12345678900')
    })