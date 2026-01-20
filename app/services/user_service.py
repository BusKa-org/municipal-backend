from werkzeug.security import generate_password_hash, check_password_hash
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
        gestor = db.session.get(User, gestor_id)
        
        if not gestor or str(gestor.role) != 'GESTOR':
            return {"error": "Apenas gestores podem cadastrar motoristas"}, 403

        prefeitura_id_obrigatorio = gestor.prefeitura_id

        try:
            if User.query.filter((User.email == data['email']) | (User.cpf == data['cpf'])).first():
                return {"error": "Email ou CPF já cadastrado"}, 400
            
            if Motorista.query.filter_by(cnh=data['cnh']).first():
                return {"error": "CNH já cadastrada"}, 400

            novo_motorista = Motorista(
                prefeitura_id=prefeitura_id_obrigatorio,
                nome=data['nome'],
                email=data['email'],
                senha_hash=generate_password_hash(data['password']),
                cpf=data['cpf'],
                telefone=data['telefone'],
                role=UserRole.MOTORISTA,
                
                cnh=data['cnh']
            )

            db.session.add(novo_motorista)
            db.session.commit()

            return {
                "message": "Motorista cadastrado com sucesso",
                "id": str(novo_motorista.usuario_id)
            }, 201

        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    @staticmethod
    def change_password(user_id, data):
        """
        Permite que qualquer usuário logado troque sua própria senha.
        Exige a senha atual por segurança.
        """
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return {"error": "Senha atual e nova senha são obrigatórias"}, 400

        user = User.query.get(user_id)
        if not user:
            return {"error": "Usuário não encontrado"}, 404

        if not check_password_hash(user.senha_hash, current_password):
            return {"error": "A senha atual está incorreta"}, 401

        user.senha_hash = generate_password_hash(new_password)
        
        try:
            db.session.commit()
            return {"message": "Senha alterada com sucesso"}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": "Erro ao atualizar senha", "details": str(e)}, 500