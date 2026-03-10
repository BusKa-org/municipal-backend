from typing import Any

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource

from app.api.contracts import aluno_contract, user_contract
from app.core.exceptions import NotFoundError, ValidationError
from app.models.base import db
from app.models.user import User
from app.schemas.aluno_schema import AlunoAccountCreateSchema
from app.schemas.user_schema import ChangePasswordSchema, MotoristaCreateSchema, UserResponseSchema
from app.services import user_service

api = Namespace("users", description="Gerenciamento de Usuários e Perfil")

# API contracts (Swagger documentation)
models = user_contract.register_models(api)
models_aluno = aluno_contract.register_models(api)

# Validation schemas (Marshmallow)
user_schema = UserResponseSchema()
list_response_schema = UserResponseSchema(many=True)
motorista_create_schema = MotoristaCreateSchema()
change_password_schema = ChangePasswordSchema()
aluno_account_create_schema = AlunoAccountCreateSchema()


@api.route("")
class UserList(Resource):
    @api.doc("list_users", responses={200: "Success", 403: "Forbidden - not a gestor"})
    @api.marshal_list_with(models["response"], code=200)
    @jwt_required()
    def get(self) -> tuple[list[dict[str, Any]], int]:
        """Lista todos os usuários da prefeitura (Apenas Gestor)"""
        current_user_id = get_jwt_identity()
        users = user_service.get_all_users(current_user_id)
        return list_response_schema.dump(users), 200


@api.route("/me")
class UserProfile(Resource):
    @api.doc("get_my_profile", responses={200: "Success", 404: "User not found"})
    @api.marshal_with(models["response"], code=200)
    @jwt_required()
    def get(self) -> tuple[dict[str, Any], int]:
        """Perfil do usuário logado"""
        current_user_id = get_jwt_identity()
        user = user_service.get_user_by_id(current_user_id)
        return user_schema.dump(user), 200


@api.route("/<string:id>")
@api.param("id", "O UUID do usuário")
class UserResource(Resource):
    @api.doc(
        "get_user_by_id",
        responses={200: "Success", 403: "Forbidden", 404: "User not found"},
    )
    @jwt_required()
    def get(self, id: str) -> tuple[dict[str, Any], int]:
        """Busca usuário por ID (próprio perfil ou mesma prefeitura se Gestor)"""
        current_user_id = get_jwt_identity()
        user = user_service.get_user_by_id(id, current_user_id)
        return user_schema.dump(user), 200


@api.route("/alunos")
class AlunoAccountCreateResource(Resource):
    @api.doc(
        "create_aluno_account",
        responses={
            201: "Aluno account created",
            400: "Validation error",
            403: "Forbidden - not a gestor",
            409: "Conflict - duplicate email/CPF",
        },
    )
    @api.expect(models_aluno["create_aluno_account_request"])
    @jwt_required()
    def post(self):
        """Gestor cria uma nova conta de aluno"""
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        errors = aluno_account_create_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        aluno = user_service.create_aluno_account(current_user_id, data)
        return {"message": "Aluno account created with success", "id": str(aluno.id)}, 201


@api.route("/motoristas")
class MotoristaCreateResource(Resource):
    @api.doc(
        "create_motorista",
        responses={
            201: "Motorista created",
            400: "Validation error",
            403: "Forbidden - not a gestor",
            409: "Conflict - duplicate email/CPF/CNH",
        },
    )
    @api.expect(models["motorista_create"])
    @jwt_required()
    def post(self) -> tuple[dict[str, str], int]:
        """Gestor cria um novo Motorista"""
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        errors = motorista_create_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        motorista = user_service.create_motorista(current_user_id, data)
        return {"message": "Motorista cadastrado com sucesso", "id": str(motorista.id)}, 201


@api.route("/change-password")
class UserChangePassword(Resource):
    @api.doc(
        "change_user_password",
        responses={
            200: "Password changed successfully",
            400: "Validation error",
            401: "Incorrect current password",
            429: "Too many attempts - rate limited",
        },
    )
    @api.expect(models["change_password"])
    @jwt_required()
    def post(self) -> tuple[dict[str, str], int]:
        """Altera a senha do usuário logado (Requer senha atual)."""
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        errors = change_password_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        user_service.change_password(current_user_id, data)
        return {"message": "Senha alterada com sucesso"}, 200


@api.route("/fcm-token")
class UserFcmToken(Resource):
    @api.doc("update_fcm_token", responses={200: "Token atualizado", 400: "Token não enviado"})
    @api.expect(models["fcm_token_request"])
    @jwt_required()
    def patch(self) -> tuple[dict[str, str], int]:
        """Atualiza o Token do Firebase (Push Notifications) do aparelho do usuário"""
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        fcm_token = data.get("fcm_token")
        if not fcm_token:
            raise ValidationError("O campo 'fcm_token' é obrigatório")

        usuario = db.session.get(User, current_user_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")

        # Atualiza o token no banco
        usuario.fcm_token = fcm_token
        db.session.commit()

        return {"message": "Token de notificação atualizado com sucesso"}, 200
