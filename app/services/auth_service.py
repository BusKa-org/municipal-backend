from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token

from ..models.user import User
from ..models.municipio import Municipio
from ..models.base import db


class AuthService:

    @staticmethod
    def login(data: dict):
        if not data or "email" not in data or "password" not in data:
            return {"error": "Email and password are required"}, 400

        email = data["email"].strip().lower()
        password = data["password"]

        user = User.query.filter_by(email=email).first()

        if not user:
            return {"error": "User not found"}, 404

        if not check_password_hash(user.senha_hash, password):
            return {"error": "Invalid credentials"}, 401

        token = create_access_token(identity=str(user.id))

        return {
            "access_token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "nome": user.nome,
                "role": user.role
            }
        }, 200

    @staticmethod
    def register_dev(data: dict):
        email = data.get("email", "").lower().strip()
        password = data.get("password", "").strip()
        nome = data.get("nome", "").strip()
        role = data.get("role", "aluno").strip()
        municipio_name = data.get("municipio", "").upper().strip()

        if not all([email, password, nome, role, municipio_name]):
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
            role=role,
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
