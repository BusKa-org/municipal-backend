from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource

from app.api.contracts import aluno_contract
from app.core.exceptions import ValidationError
from app.schemas.aluno_schema import AlunoCreateSchema, AlunoResponseSchema, AlunoUpdateSchema
from app.services import aluno_service

api = Namespace("alunos", description="Área do Aluno (App)")

# API contracts (Swagger documentation)
models = aluno_contract.register_models(api)

# Validation schemas (Marshmallow)
create_schema = AlunoCreateSchema()
update_schema = AlunoUpdateSchema()
response_schema = AlunoResponseSchema()
list_response_schema = AlunoResponseSchema(many=True)


@api.route("/signup")
class AlunoSignupResource(Resource):
    @api.doc("aluno_signup", security=[])
    @api.expect(models["create_request"])
    @api.marshal_with(models["response"], code=201)
    def post(self):
        """Auto-cadastro do Aluno (Público)"""
        data = request.get_json()

        errors = create_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        aluno = aluno_service.auto_cadastro(data)
        return response_schema.dump(aluno), 201


@api.route("/me")
class AlunoMeResource(Resource):
    @api.doc("aluno_profile")
    @api.expect(models["update_request"])
    @api.marshal_with(models["response"], code=200)
    @jwt_required()
    def put(self):
        """Aluno atualiza seu perfil (Dados Pessoais + Endereço)"""
        user_id = get_jwt_identity()
        data = request.get_json()

        errors = update_schema.validate(data)
        if errors:
            raise ValidationError("Erro de validação", details=errors)

        aluno = aluno_service.update_me(user_id, data)
        return response_schema.dump(aluno), 200

    @api.doc("aluno_delete")
    @jwt_required()
    def delete(self):
        """Aluno exclui sua conta"""
        user_id = get_jwt_identity()
        aluno_service.delete_me(user_id)
        return {"message": "Conta excluída com sucesso"}, 200


@api.route("/")
class AlunoListResource(Resource):
    @api.doc("list_alunos_gestor")
    @jwt_required()
    def get(self):
        """Gestor vê lista de alunos cadastrados"""
        user_id = get_jwt_identity()
        alunos = aluno_service.list_alunos_gestor(user_id)
        return list_response_schema.dump(alunos), 200
