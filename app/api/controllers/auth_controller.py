from typing import Any

from flask import request
from flask_restx import Namespace, Resource

from app.api.contracts import auth_contract
from app.schemas.auth_schema import LoginRequestSchema, TokenResponseSchema
from app.services import auth_service

api = Namespace("auth", description="Autenticação e gerenciamento de sessão")

# Register documentation models
models = auth_contract.register_models(api)

login_request_schema = LoginRequestSchema()
token_response_schema = TokenResponseSchema()


@api.route("/login")
class AuthLogin(Resource):
    @api.doc(
        "auth_login",
        responses={
            200: "Login successful - returns JWT token",
            400: "Validation error",
            401: "Invalid credentials",
            429: "Too many login attempts - rate limited",
        },
    )
    @api.expect(models["login_request"])
    @api.response(200, "Success", models["token_response"])
    def post(self) -> tuple[dict[str, Any], int]:
        """
        Authenticate user and get JWT token.

        Use the returned token in the `Authorization` header for authenticated requests:
        `Authorization: Bearer <token>`
        """
        data = request.get_json(silent=True) or {}
        payload = login_request_schema.load(data)

        response = auth_service.login_user(payload)
        return token_response_schema.dump(response), 200
