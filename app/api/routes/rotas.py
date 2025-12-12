from flask import Blueprint
from flask_jwt_extended import jwt_required
from flasgger import swag_from

from ..controllers.rotas_controller import RotasController

rotas_bp = Blueprint("rotas", __name__)
docs_prefix = "../../../../../docs/endpoints/"


@rotas_bp.route("/", methods=["GET"])
@swag_from(docs_prefix + "motorista-listar_rotas.yml")
@jwt_required()
def list_all_rotas():
    return RotasController.list_all_rotas()

@rotas_bp.route("/", methods=["POST"])
@swag_from(docs_prefix + "motorista-criar_rota.yml")
@jwt_required()
def create_rota():
    return RotasController.create_rota()

@rotas_bp.route("/<int:rota_id>/ponto", methods=["POST"])
@swag_from(docs_prefix + "motorista-adicionar_ponto.yml")
@jwt_required()
def add_ponto(rota_id):
    return RotasController.add_ponto(rota_id)

@rotas_bp.route("/<int:rota_id>/inscricao", methods=["PUT"])
@swag_from(docs_prefix+'aluno-inscricao_rota.yml')
@jwt_required()
def inscricao_aluno_rota(rota_id):
    return RotasController.inscricao_aluno_rota(rota_id)
