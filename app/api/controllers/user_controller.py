from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity

from ...services.user_service import UserService


class UserController:

    @staticmethod
    def get_current_user():
        user = UserService.get_user_by_id(get_jwt_identity())
        if not user:
            return jsonify({"error": "user not found"}), 404

        return jsonify({
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "municipio": user.municipio_id,
            "role": user.role
        }), 200

    @staticmethod
    def update_user():
        identity = get_jwt_identity()
        data = request.get_json()

        result, status = UserService.update_user(identity, data)
        return jsonify(result), status

    def create_motorista():
        identity = get_jwt_identity()
        data = request.get_json()

        result, status = UserService.create_motorista(identity, data)
        return jsonify(result), status


    @staticmethod
    def list_users():
        identity = get_jwt_identity()
        result, status = UserService.list_users(identity)
        return jsonify(result), status
