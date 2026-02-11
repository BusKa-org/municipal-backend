from typing import Any

from flask import request
from flask_restx import Namespace, Resource

from app.api.contracts import auth_contract
from app.core.exceptions import ValidationError
from app.services import auth_service

api = Namespace("auth", description="Autenticação e gerenciamento de sessão")

# Register documentation models
models = auth_contract.register_models(api)


@api.route("/login")
class AuthLogin(Resource):
    @api.doc(
        "auth_login",
        responses={
            200: "Login successful - returns JWT token",
            400: "Missing email or password",
            401: "Invalid credentials",
            429: "Too many login attempts - rate limited",
        },
    )
    @api.expect(models["login_request"])
    @api.marshal_with(models["token_response"], code=200)
    def post(self) -> tuple[dict[str, Any], int]:
        """
        Authenticate user and get JWT token.

        Use the returned token in the `Authorization` header for authenticated requests:
        `Authorization: Bearer <token>`
        """
        data = request.get_json() or {}

        if not data.get("email") or not data.get("password"):
            raise ValidationError("Email e senha são obrigatórios")

        return auth_service.login_user(data), 200
