from flask import Blueprint
from flask_jwt_extended import jwt_required
from flasgger import swag_from

from ..controllers.viagens_controller import ViagensController

viagens_bp = Blueprint("viagens", __name__)
docs_prefix = "../../../../../docs/endpoints/"


@viagens_bp.route("/", methods=["GET"])
@swag_from(docs_prefix + "motorista-listar_viagens.yml")
@jwt_required()
def listar_viagens():
    return ViagensController.list_all_viagens()

@viagens_bp.route("/<int:viagem_id>/inscricao", methods=["GET"])
@swag_from(docs_prefix+'aluno-presenca_viagem.yml')
@jwt_required()
def inscricao_viagem(viagem_id):
    return ViagensController.inscricao_aluno_viagem(viagem_id)

@viagens_bp.route("/<int:viagem_id>/iniciar", methods=["POST"])
@swag_from(docs_prefix + "motorista-iniciar_viagem.yml")
@jwt_required()
def iniciar_viagem(viagem_id):
    return ViagensController.start_viagem(viagem_id)


@viagens_bp.route("/<int:viagem_id>/finalizar", methods=["POST"])
@swag_from(docs_prefix + "motorista-finalizar_viagem.yml")
@jwt_required()
def finalizar_viagem(viagem_id):
    return ViagensController.end_viagem(viagem_id)
