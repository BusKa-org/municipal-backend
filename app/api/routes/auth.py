from flask import Blueprint
from flasgger import swag_from

from ..controllers.auth_controller import AuthController

auth_bp = Blueprint("auth", __name__)
docs_prefix = "../../../docs/endpoints/"


@auth_bp.route("/login", methods=["POST"])
@swag_from(docs_prefix + "auth-login.yml")
def login():
    return AuthController.login()


@auth_bp.route("/register", methods=["POST"])
@swag_from(docs_prefix + "auth-register.yml")
def register():
    return AuthController.register()


@auth_bp.route("/register_dev", methods=["POST"])
@swag_from(docs_prefix + "auth-register.yml")
def register_dev():
    return AuthController.register_dev()
