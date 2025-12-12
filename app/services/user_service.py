from werkzeug.security import generate_password_hash
from flask import request, jsonify

from ..models.user import User
from ..models.municipio import Municipio
from ..models.base import db
import uuid


class UserService:

    @staticmethod
    def get_user_by_id(user_id: uuid):
        return User.query.get(user_id)

    @staticmethod
    def update_user(user_id: uuid, data: dict):
        user = User.query.get(user_id)
        if not user:
            return {"error": "user not found"}, 404

        nome = data.get("nome")
        email = data.get("email")
        password = data.get("password")
        municipio_id = data.get("municipio")

        # Apply updates
        if nome:
            user.nome = nome.strip()

        if email:
            user.email = email.lower().strip()

        if password:
            user.senha_hash = generate_password_hash(password.strip())

        if municipio_id:
            municipio = Municipio.query.filter_by(id=municipio_id).first()
            if not municipio:
                return {"error": f"Municipio with Name '{municipio_name}' not found"}, 404
            user.municipio_id = municipio.id

        db.session.commit()
        return {"message": "user updated successfully."}, 200

    @staticmethod
    def create_user(data):
        email = data.get("email", "").lower().strip()
        password = data.get("password", "").strip()
        nome = data.get("nome", "").strip()
        municipio_name = data.get("municipio", "").upper().strip()

        if not all([email, password, nome, municipio_name]):
            return {"error": "Missing required field"}, 400

        if User.query.filter_by(email=email).first():
            return {"error": "User already exists"}, 400

        municipio = Municipio.query.filter_by(nome=municipio_name).first()
        if not municipio:
            return {"error": f"Municipio with name '{municipio_name}' not found"}, 404

        hashed_pw = generate_password_hash(password)

        new_user = User(
            nome=nome,
            email=email,
            senha_hash=hashed_pw,
            role="aluno",
            municipio=municipio,
        )

        db.session.add(new_user)
        db.session.commit()

        return {
            "message": "User registered successfully.",
            "user": {
                "id": new_user.id,
                "nome": new_user.nome,
                "email": new_user.email,
                "role": new_user.role,
                "municipio": {
                    "id": municipio.id,
                    "nome": municipio.nome,
                    "uf": municipio.uf
                }
            }
        }, 201

    @staticmethod
    def create_motorista(gestor_id, data):
        """Create a new motorista (driver) for this municipality."""
        user = User.query.get(gestor_id)
    
        if not user or not user.is_gestor():
            return {"error": "Access restricted to gestores"}, 403
    
        data = request.get_json()
        nome = data.get("nome").strip()
        email = data.get("email").strip()
        password = data.get("password").strip()
    
        if not all([nome, email, password]):
            return {"error": "Nome, email e senha são obrigatórios"}, 400
    
        hashed_pw = generate_password_hash(password)
    
        motorista = User(
            nome=nome,
            email=email.lower(),
            senha_hash=hashed_pw,
            role="motorista",
            municipio_id=user.municipio_id,
        )
    
        db.session.add(motorista)
        db.session.commit()
    
        return {"message": "Motorista criado com sucesso."}, 201

    @staticmethod
    def list_users(gestor_id):
        user = User.query.get(gestor_id)

        if not user or user.is_gestor():
            return {"error": "Unauthorized"}, 403

        users = User.query.all()
        return ([
            {
                "id": u.id,
                "nome": u.nome,
                "email": u.email,
                "municipio": u.municipio_id,
                "role": u.role,
            }
            for u in users
        ], 200)
