from werkzeug.security import generate_password_hash
from ..models.user import User, Motorista, Aluno, Gestor
from ..models.base import db
from ..models.enum import UserRole 
import uuid

class UserService:

    @staticmethod
    def get_all_users():
        return User.query.all()

    @staticmethod
    def get_user_by_id(user_id: uuid):
        return User.query.get(user_id)

    @staticmethod
    def create_user(data):
        email = data.get("email", "").lower().strip()
        password = data.get("password", "").strip()
        nome = data.get("nome", "").strip()
        cpf = data.get("cpf", "").strip()
        telefone = data.get("telefone", "").strip()
        
        role_str = data.get("role", "ALUNO").upper().strip()
        try:
            role_enum = UserRole(role_str)
        except ValueError:
            return {"error": "Perfil inválido. Use: ALUNO, MOTORISTA, GESTOR"}, 400

        if not all([email, password, nome, cpf]):
            return {"error": "Dados incompletos (Email, Senha, Nome, CPF)"}, 400

        if User.query.filter((User.email == email) | (User.cpf == cpf)).first():
            return {"error": "Usuário já existe (Email ou CPF duplicado)"}, 400

        hashed_pw = generate_password_hash(password)

        if role_enum == UserRole.GESTOR:
            new_user = Gestor(
                nome=nome, email=email, senha_hash=hashed_pw,
                cpf=cpf, telefone=telefone, role=role_enum
            )
        elif role_enum == UserRole.ALUNO:
            new_user = Aluno(
                nome=nome, email=email, senha_hash=hashed_pw,
                cpf=cpf, telefone=telefone, role=role_enum
            )
        else:
            new_user = User(
                nome=nome, email=email, senha_hash=hashed_pw,
                cpf=cpf, telefone=telefone, role=role_enum
            )

        db.session.add(new_user)
        db.session.commit()

        return new_user, 201

    @staticmethod
    def update_user(user_id: uuid, data: dict):
        user = User.query.get(user_id)
        if not user:
            return {"error": "User not found"}, 404

        nome = data.get("nome")
        email = data.get("email")
        password = data.get("password")
        telefone = data.get("telefone")

        if nome:
            user.nome = nome.strip()

        if email:
            email_limpo = email.lower().strip()
            existing = User.query.filter_by(email=email_limpo).first()
            if existing and existing.id != user_id:
                return {"error": "Email já está em uso"}, 400
            user.email = email_limpo

        if password:
            user.senha_hash = generate_password_hash(password.strip())
            
        if telefone:
            user.telefone = telefone.strip()

        db.session.commit()
        return {"message": "User updated successfully."}, 200

    @staticmethod
    def create_motorista(gestor_id, data):
        gestor = User.query.get(gestor_id)
        if not gestor or not gestor.is_gestor(): 
            return {"error": "Apenas gestores podem criar motoristas"}, 403
    
        nome = data.get("nome", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        cpf = data.get("cpf", "").strip()
        cnh = data.get("cnh", "").strip()

        if not all([nome, email, password, cpf, cnh]):
            return {"error": "Nome, email, senha, CPF e CNH são obrigatórios"}, 400
    
        if User.query.filter((User.email == email) | (User.cpf == cpf)).first():
            return {"error": "Usuário já existe"}, 400

        if Motorista.query.filter_by(cnh=cnh).first():
             return {"error": "CNH já cadastrada"}, 400      

        hashed_pw = generate_password_hash(password)
    
        novo_motorista = Motorista(
            nome=nome,
            email=email.lower(),
            cpf=cpf,
            senha_hash=hashed_pw,
            role=UserRole.MOTORISTA,
            cnh=cnh 
        )
    
        db.session.add(novo_motorista)
        db.session.commit()
    
        return {"message": "Motorista criado com sucesso."}, 201