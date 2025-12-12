from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity

from ...services.viagens_service import ViagensService


class ViagensController:

    @staticmethod
    def list_all_viagens():
        user_id = get_jwt_identity()
        result, status = ViagensService.list_all_viagens(user_id)
        return jsonify(result), status

    @staticmethod
    def list_my_viagens():
        user_id = get_jwt_identity()
        result, status = ViagensService.list_my_viagens(user_id)
        return jsonify(result), status

    @staticmethod
    def presenca_aluno_viagem(viagem_id):
        user_id = get_jwt_identity()
        result, status = ViagensService.presenca_aluno_viagem(user_id, viagem_id)
        return jsonify(result), status

    @staticmethod
    def create_viagem(rota_id):
        result, status = ViagensService.create_viagem(rota_id)
        return jsonify(result), status

    @staticmethod
    def start_viagem(viagem_id):
        user_id = get_jwt_identity()
        result, status = ViagensService.start_viagem(user_id, viagem_id)
        return jsonify(result), status

    @staticmethod
    def finalizar_viagem(viagem_id):
        user_id = get_jwt_identity()
        result, status = ViagensService.end_viagem(user_id, viagem_id)
        return jsonify(result), status
