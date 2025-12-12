from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity

from ...services.rotas_service import RotasService


class RotasController:

    @staticmethod
    def list_all_rotas():
        user_id = get_jwt_identity()
        result, status = RotasService.list_all_rotas(user_id)
        return jsonify(result), status

    @staticmethod
    def list_my_rotas():
        user_id = get_jwt_identity()
        result, status = RotasService.list_my_rotas(user_id)
        return jsonify(result), status

    @staticmethod
    def inscricao_aluno_rota(rota_id):
        user_id = get_jwt_identity()
        result, status = RotasService.inscricao_aluno_viagem(user_id, rota_id)
        return jsonify(result), status

    @staticmethod
    def create_rota():
        user_id = get_jwt_identity()
        data = request.get_json()
        result, status = RotasService.create_rota(user_id, data)
        return jsonify(result), status

    @staticmethod
    def add_ponto(rota_id):
        user_id = get_jwt_identity()
        data = request.get_json()
        result, status = RotasService.add_ponto(user_id, rota_id, data)
        return jsonify(result), status
