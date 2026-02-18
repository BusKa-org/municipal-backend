from typing import Any

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource

from app.api.contracts import aluno_contract
from app.schemas.aluno_schema import (
    AlunoListResponseSchema,
    AlunoMeUpdateRequestSchema,
    AlunoResponseSchema,
    AlunoSelfSignupRequestSchema,
)
from app.services import aluno_service

api = Namespace("alunos", description="Área do Aluno (App)")

# API contracts (Swagger documentation)
models = aluno_contract.register_models(api)

# Validation schemas (Marshmallow)
self_signup_schema = AlunoSelfSignupRequestSchema()
me_update_schema = AlunoMeUpdateRequestSchema()
aluno_response_schema = AlunoResponseSchema()
aluno_list_response_schema = AlunoListResponseSchema()


@api.route("/signup")
class AlunoSignupResource(Resource):
    @api.doc("aluno_signup", security=[])
    @api.expect(models["self_signup_request"])
    @api.response(201, "Success", models["aluno_response"])
    def post(self):
        """Auto-cadastro do Aluno (Público)"""
        data = request.get_json(silent=True) or {}
        payload = self_signup_schema.load(data)
        aluno = aluno_service.auto_cadastro(payload)
        return aluno_response_schema.dump(aluno), 201


@api.route("/me")
class AlunoMeResource(Resource):
    @api.doc("aluno_profile")
    @api.expect(models["me_update_request"])
    @api.response(200, "Success", models["aluno_response"])
    @jwt_required()
    def put(self) -> tuple[dict[str, Any], int]:
        """Aluno atualiza seu perfil (Dados Pessoais + Endereço)"""
        user_id = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        payload = me_update_schema.load(data)

        aluno = aluno_service.update_me(user_id, payload)
        return aluno_response_schema.dump(aluno), 200

    @api.doc("aluno_delete")
    @api.response(200, "Success")
    @jwt_required()
    def delete(self) -> tuple[dict[str, Any], int]:
        """Aluno exclui sua conta"""
        user_id = get_jwt_identity()
        aluno_service.delete_me(user_id)
        return {"message": "Conta excluída com sucesso"}, 200


@api.route("/")
class AlunoListResource(Resource):
    @api.doc("list_alunos_gestor")
    @api.response(200, "Success", models["aluno_list_response"])
    @jwt_required()
    def get(self) -> tuple[dict[str, Any], int]:
        """Gestor vê lista de alunos cadastrados"""
        user_id = get_jwt_identity()
        alunos = aluno_service.list_alunos_gestor(user_id)
        return (
            aluno_list_response_schema.dump(
                {
                    "items": alunos,
                    "total": len(alunos),
                }
            ),
            200,
        )
