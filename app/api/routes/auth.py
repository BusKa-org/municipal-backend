from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flasgger import swag_from
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta

from ...models.base import db
from ...models.user import User
from ...models.municipio import Municipio

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
@swag_from('../../../../docs/auth-login.yml')
def login():
    """
    Authenticate user and return JWT token
    """
    data = request.get_json()

    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password are required"}), 400

    email = data["email"].strip().lower()
    password = data["password"]

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not check_password_hash(user.senha_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "nome": user.nome,
            "role": user.role
        }
    }), 200

@auth_bp.route("/register", methods=["POST"])
@swag_from('../../../../docs/auth-register.yml')
def register():
    data = request.get_json()
    email = data.get("email", "").lower().strip()
    password = data.get("password","").strip()
    nome = data.get("nome","").strip()
    role = data.get("role", "aluno").strip()
    municipio_name = data.get("municipio", "").upper().strip()


    if not all([email,password,nome,role,municipio_name]):
        return jsonify({"error": "Missing required field"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 400

    municipio = Municipio.query.filter_by(nome=municipio_name).first()
    if not municipio:
        return jsonify({"error": f"Municipio with Name '{municipio_name}' not found"}), 404

    hashed_pw = generate_password_hash(password)

    # TODO: passar isso aqui pro /service
    new_user = User(
        nome=nome, 
        email=email, 
        senha_hash=hashed_pw, 
        role=role,      # TODO: falha de seguranca -> o aluno pode descobrir e se cadastrar como gestor
                        #       verificar a regra de negocio -> eh dito que o gestor deve ter controle do cadastro dos motoristas
                        #                                       mas o motorista poderia se cadastrar sozinho?
        municipio=municipio,
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully.",
        "user": {
            "id": new_user.id,
            "nome": new_user.nome,
            "email": new_user.email,
            "role": new_user.role,
            "municipio": {"id": municipio.id, "nome": municipio.nome, "uf": municipio.uf}
        }
    }), 201
