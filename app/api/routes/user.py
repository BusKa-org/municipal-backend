from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from flasgger import swag_from

from ...models.base import db
from ...models.municipio import Municipio
from ..controllers.user_controller import UserController

user_bp = Blueprint("user", __name__)
docs_prefix = '../../../../../docs/endpoints/' 


@user_bp.route("/motorista", methods=["POST"])
@swag_from(docs_prefix + 'gestor-criar_motoristas.yml')
@jwt_required()
def create_motorista():
    return UserController.create_motorista()

@user_bp.route("/", methods=["GET"])
@swag_from(docs_prefix + 'user-list.yml')
@jwt_required()
def list_users():
    role_filter = request.args.get('role')
    return UserController.list_users()
