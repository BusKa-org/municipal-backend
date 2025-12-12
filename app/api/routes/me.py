from flask import Blueprint
from flask_jwt_extended import jwt_required
from flasgger import swag_from

from ..controllers.user_controller import UserController
from ..controllers.rotas_controller import RotasController
from ..controllers.viagens_controller import ViagensController

me_bp = Blueprint("me", __name__)
docs_prefix = "../../../../../docs/endpoints/"


@me_bp.route("/", methods=["GET"])
@swag_from(docs_prefix + 'user-me.yml')
@jwt_required()
def get_current_user():
    return UserController.get_current_user()


@me_bp.route("/", methods=["PUT"])
@swag_from(docs_prefix + 'user-update.yml')
@jwt_required()
def update_user():
    return UserController.update_user()

@me_bp.route("/rotas", methods=["GET"])
@swag_from(docs_prefix + "aluno-listar_rotas.yml")
@jwt_required()
def list_my_rotas():
    return RotasController.list_my_rotas()

@me_bp.route("/viagens", methods=["GET"])
@swag_from(docs_prefix + "aluno-listar_viagens.yml")
@jwt_required()
def list_my_viagens():
    return ViagensController.list_my_viagens()

