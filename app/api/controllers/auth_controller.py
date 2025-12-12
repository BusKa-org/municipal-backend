from flask import request, jsonify

from ...services.auth_service import AuthService
from ...services.user_service import UserService


class AuthController:

    @staticmethod
    def login():
        data = request.get_json()
        result, status = AuthService.login(data)
        return jsonify(result), status

    @staticmethod
    def register():
        data = request.get_json()
        result, status = UserService.create_user(data)
        return jsonify(result), status

    @staticmethod
    def register_dev():
        data = request.get_json()
        result, status = AuthService.register_dev(data)
        return jsonify(result), status
