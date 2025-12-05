from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from werkzeug.security import generate_password_hash

from ...models.base import db
from ...models.user import User
from ...models.municipio import Municipio

user_bp = Blueprint("user", __name__)

@user_bp.route("/me", methods=["GET"])
@swag_from('../../../../../docs/user-me.yml')
@jwt_required()
def get_current_user():
    """Return the authenticated user's profile."""
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user:
        return jsonify({"error": "user not found"}), 404

    return jsonify({
        "id": user.id,
        "nome": user.nome,
        "email": user.email,
        "municipio": user.municipio_id,
        "role": user.role
    }), 200


@user_bp.route("/update", methods=["PUT"])
@swag_from('../../../../../docs/user-update.yml')
@jwt_required()
def update_user():
    """Allow user to update their profile."""
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user:
        return jsonify({"error": "user not found"}), 404

    data = request.get_json()

    nome = data.get("nome").strip()
    email = data.get("email").strip()
    password = data.get("password").strip()
    municipio_name = data.get("municipio").upper().strip()

    if nome:
        user.nome = nome
    if email:
        user.email = email.lower()
    if password:
        user.senha_hash = generate_password_hash(password)
    if municipio_name:
        municipio = Municipio.query.filter_by(nome=municipio_name).first()
        if not municipio:
            return jsonify({"error": f"Municipio with Name '{municipio_name}' not found"}), 404
        user.municipio_id = municipio.id

    db.session.commit()
    return jsonify({"message": "user updated successfully."}), 200


@user_bp.route("/list", methods=["GET"])
@swag_from('../../../../../docs/user-list.yml')
@jwt_required()
def list_users():
    """List all users (restricted to gestor role)."""
    identity = get_jwt_identity()
    current_user = User.query.get(int(identity))

    if not current_user or current_user.role != "gestor":
        return jsonify({"error": "Unauthorized"}), 403

    users = User.query.all()
    return jsonify([
        {
            "id": u.id,
            "nome": u.nome,
            "email": u.email,
            "municipio": u.municipio_id,
            "role": u.role
        } for u in users
    ]), 200
