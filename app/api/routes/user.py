from flask import Blueprint
from flask_jwt_extended import jwt_required
from flasgger import swag_from

from ...models.base import db
from ...models.municipio import Municipio
from ..controllers.user_controller import UserController

user_bp = Blueprint("user", __name__)
docs_prefix = '../../../../../docs/endpoints/' 

@user_bp.route("/me", methods=["GET"])
@swag_from(docs_prefix + 'user-me.yml')
@jwt_required()
def get_current_user():
    return UserController.get_current_user()


@user_bp.route("/update", methods=["PUT"])
@swag_from(docs_prefix + 'user-update.yml')
@jwt_required()
def update_user():
    return UserController.update_user()


@user_bp.route("/list", methods=["GET"])
@swag_from(docs_prefix + 'user-list.yml')
@jwt_required()
def list_users():
    return UserController.list_users()
