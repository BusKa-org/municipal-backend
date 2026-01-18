from app import db
from app.models.user import User, Aluno, Motorista, Gestor
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError

class AuthService:
            
    @staticmethod
    def login_user(data):
        user = User.query.filter_by(email=data.get('email')).first()

        if user and check_password_hash(user.senha_hash, data.get('password')):
            access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
            
            return {
                "message": "Login successful",
                "token": access_token,
                "user": {
                    "id": str(user.id),
                    "nome": user.nome,
                    "email": user.email,
                    "role": user.role
                }
            }, 200
        
        return {"error": "Invalid credentials"}, 401

    @staticmethod
    def register_user(data):
        try:
            if User.query.filter((User.email == data['email']) | (User.cpf == data['cpf'])).first():
                return {"error": "Email or CPF already registered"}, 400

            new_user = User(
                nome=data['nome'],
                email=data['email'],
                senha_hash=generate_password_hash(data['password']),
                telefone=data.get('telefone'),
                cpf=data['cpf']
            )

            db.session.add(new_user)
            db.session.flush() 

            role = data.get('role', '').lower()
            
            if role == 'aluno':
                profile = Aluno(
                    usuario_id=new_user.id,
                    matricula=data.get('matricula'),
                    nome_pai=data.get('nome_pai'),
                    nome_mae=data.get('nome_mae')
                )
            elif role == 'motorista':
                if not data.get('cnh'):
                    db.session.rollback()
                    return {"error": "CNH is required for Motorista"}, 400
                profile = Motorista(usuario_id=new_user.id, cnh=data.get('cnh'))
            elif role == 'gestor':
                profile = Gestor(usuario_id=new_user.id, matricula=data.get('matricula'), salario=data.get('salario'))
            else:
                db.session.rollback()
                return {"error": "Invalid role"}, 400

            db.session.add(profile)
            db.session.commit()

            return {"message": "User created successfully", "id": str(new_user.id)}, 201

        except IntegrityError:
            db.session.rollback()
            return {"error": "Database error"}, 500
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
