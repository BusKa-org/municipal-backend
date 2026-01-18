from flask_restx import Namespace, fields

class AuthContract:
    api = Namespace('auth', description='Autenticação e Registro de Usuários')

    login_request = api.model('Login', {
        'email': fields.String(required=True, description='Email do usuário', example='joao@email.com'),
        'password': fields.String(required=True, description='Senha do usuário', example='senhaForte123')
    })

    register_request = api.model('Register', {
        'nome': fields.String(required=True, description='Nome completo', example='João da Silva'),
        'email': fields.String(required=True, description='Email único', example='joao@email.com'),
        'password': fields.String(required=True, description='Senha', example='senhaForte123'),
        'cpf': fields.String(required=True, description='CPF (apenas números)', example='12345678900'),
        'telefone': fields.String(description='Telefone para contato', example='11999999999'),
        'role': fields.String(required=True, description='Tipo de perfil', enum=['aluno', 'motorista', 'gestor'], example='aluno'),
        
        'matricula': fields.String(description='(Para Aluno/Gestor) Matrícula da instituição', example='2024001'),
        'nome_pai': fields.String(description='(Para Aluno) Nome do pai'),
        'nome_mae': fields.String(description='(Para Aluno) Nome da mãe'),
        'cnh': fields.String(description='(Para Motorista) Número da CNH'),
        'salario': fields.Float(description='(Para Gestor) Salário')
    })