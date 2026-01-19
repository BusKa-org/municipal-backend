from app import db
from app.models.user import User, Aluno, Motorista, Gestor
from app.models.enum import UserRole
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError
from app.models.prefeitura import Prefeitura

class AuthService:
            
    @staticmethod
    def login_user(data):
        user = User.query.filter_by(email=data.get('email')).first()

        if user and check_password_hash(user.senha_hash, data.get('password')):
            access_token = create_access_token(identity=str(user.id), additional_claims={"role": str(user.role)})
            
            return {
                "message": "Login successful",
                "token": access_token,
                "user": {
                    "id": str(user.id),
                    "nome": user.nome,
                    "email": user.email,
                    "role": str(user.role)
                }
            }, 200
        
        return {"error": "Invalid credentials"}, 401

    @staticmethod
    def register_user(data):
        try:
            prefeitura_id = data.get('prefeitura_id')
            if not prefeitura_id:
                return {"error": "Prefeitura ID is required"}, 400
            
            if not Prefeitura.query.get(prefeitura_id):
                return {"error": "Prefeitura not found"}, 404
            
            if User.query.filter((User.email == data['email']) | (User.cpf == data['cpf'])).first():
                return {"error": "Email or CPF already registered"}, 400

            hashed_pw = generate_password_hash(data['password'])
            role_str = data.get('role', 'ALUNO').upper()
            
            try:
                role_enum = UserRole(role_str)
            except ValueError:
                return {"error": "Invalid role. Use: ALUNO, MOTORISTA, GESTOR"}, 400

            if role_enum == UserRole.ALUNO:
                new_user = Aluno(
                    prefeitura_id=prefeitura_id,
                    nome=data['nome'],
                    email=data['email'],
                    senha_hash=hashed_pw,
                    telefone=data.get('telefone'),
                    cpf=data['cpf'],
                    role=role_enum,
                    matricula=data.get('matricula'),
                    nome_pai=data.get('nome_pai'),
                    nome_mae=data.get('nome_mae')
                )
            
            elif role_enum == UserRole.MOTORISTA:
                if not data.get('cnh'):
                    return {"error": "CNH is required for Motorista"}, 400
                
                if Motorista.query.filter_by(cnh=data.get('cnh')).first():
                    return {"error": "CNH already registered"}, 400

                new_user = Motorista(
                    prefeitura_id=prefeitura_id,
                    nome=data['nome'],
                    email=data['email'],
                    senha_hash=hashed_pw,
                    telefone=data.get('telefone'),
                    cpf=data['cpf'],
                    role=role_enum,
                    cnh=data.get('cnh')
                )

            elif role_enum == UserRole.GESTOR:
                new_user = Gestor(
                    prefeitura_id=prefeitura_id,
                    nome=data['nome'],
                    email=data['email'],
                    senha_hash=hashed_pw,
                    telefone=data.get('telefone'),
                    cpf=data['cpf'],
                    role=role_enum,
                    matricula=data.get('matricula'),
                    salario=data.get('salario')
                )
            else:
                new_user = User(
                    nome=data['nome'],
                    email=data['email'],
                    senha_hash=hashed_pw,
                    telefone=data.get('telefone'),
                    cpf=data['cpf'],
                    role=role_enum
                )

            db.session.add(new_user)
            db.session.commit()

            return {"message": "User created successfully", "id": str(new_user.id)}, 201

        except IntegrityError as e:
            db.session.rollback()
            print(f"DB ERROR: {e}")
            return {"error": "Database integrity error"}, 400
        except Exception as e:
            db.session.rollback()
            print(f"SERVER ERROR: {e}")
            return {"error": str(e)}, 500